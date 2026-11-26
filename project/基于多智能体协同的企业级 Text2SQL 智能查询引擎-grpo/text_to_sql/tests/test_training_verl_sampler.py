import json
import importlib.util
import sys
import tempfile
import types
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch


class FakeReplayBuffer:
    def __init__(self, refill_fn, **kwargs):
        self.refill_fn = refill_fn
        self.init_kwargs = kwargs
        self.dispatches = []
        self.partitions = defaultdict(dict)
        self._dapo_classification_cache = defaultdict(dict)

    def sample(self, global_steps, partition_id, batch_size):
        for prompt_count in self.dispatches:
            self.refill_fn(prompt_count)
        return (global_steps, partition_id, batch_size), {}

    def _evict_terminal_groups(self, global_steps, partition_id, eviction_reasons):
        return set(eviction_reasons[1]), 0, len(eviction_reasons[1]), {}


class FakeTransferData:
    def __init__(self, values):
        self.values = values

    def get(self, name):
        return self.values.get(name)

    def select(self, name):
        return self

    def to_padded_tensor(self, padding):
        return {"responses": self.values["responses"]}


class FakeTokenizer:
    pad_token_id = 0

    def batch_decode(self, response_ids, skip_special_tokens):
        return [f"decoded-{ids[-1]}" for ids in response_ids]


class TestBoundedReplayBuffer(unittest.TestCase):
    def _load_sampler_class(self):
        replay_buffer_module = types.ModuleType("verl.trainer.ppo.v1.replay_buffer")
        replay_buffer_module.ReplayBuffer = FakeReplayBuffer
        modules = {
            "verl": types.ModuleType("verl"),
            "verl.trainer": types.ModuleType("verl.trainer"),
            "verl.trainer.ppo": types.ModuleType("verl.trainer.ppo"),
            "verl.trainer.ppo.v1": types.ModuleType("verl.trainer.ppo.v1"),
            "verl.trainer.ppo.v1.replay_buffer": replay_buffer_module,
        }
        module_path = (
            Path(__file__).resolve().parents[1] / "training" / "verl_sampler.py"
        )
        spec = importlib.util.spec_from_file_location("test_verl_sampler_module", module_path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(module)
        return module.BoundedReplayBuffer

    def _build_sampler(self, refill_calls, sft_path="sft.jsonl", bad_case_path="bad.jsonl"):
        sampler_class = self._load_sampler_class()
        return sampler_class(
            trainer_mode="sync",
            trainer_config={},
            max_off_policy_threshold=1,
            max_off_policy_strategy="wait",
            sampler_kwargs={
                "filter_groups_metric": "execution_correct",
                "max_num_gen_batches": 2,
                "max_inflight_gen_batches": 2,
                "train_batch_size": 5,
                "sync_refill_failed_groups": False,
                "tokenizer_path": "models/dpo_merged",
                "sft_backflow_path": sft_path,
                "bad_case_backflow_path": bad_case_path,
            },
            refill_fn=refill_calls.append,
        )

    def test_refill_budget_is_hard_bounded_per_training_sample(self):
        refill_calls = []
        sampler = self._build_sampler(refill_calls)
        sampler.dispatches = [3, 3]

        with self.assertRaisesRegex(RuntimeError, "exhausted the refill budget"):
            sampler.sample(global_steps=1, partition_id="train", batch_size=5)

        self.assertEqual(refill_calls, [3])
        self.assertEqual(
            sampler.init_kwargs["filter_groups_metric"],
            "execution_correct",
        )
        self.assertEqual(sampler.init_kwargs["max_inflight_gen_batches"], 2)

    def test_refill_budget_resets_for_each_training_sample(self):
        refill_calls = []
        sampler = self._build_sampler(refill_calls)
        sampler.dispatches = [4]

        sampler.sample(global_steps=1, partition_id="train", batch_size=5)
        sampler.sample(global_steps=2, partition_id="train", batch_size=5)

        self.assertEqual(refill_calls, [4, 4])

    def test_filtered_groups_are_persisted_before_upstream_eviction(self):
        with tempfile.TemporaryDirectory() as tmp:
            sft_path = Path(tmp) / "sft.jsonl"
            bad_path = Path(tmp) / "bad.jsonl"
            sampler = self._build_sampler([], str(sft_path), str(bad_path))
            sampler._tokenizer = FakeTokenizer()
            sampler.partitions["train"]["abc_0_0"] = {"status": "finished"}
            sampler._dapo_classification_cache["train"]["abc"] = 1.0
            transfer_queue = types.ModuleType("transfer_queue")
            transfer_queue.kv_batch_get = lambda **_: FakeTransferData(
                {
                    "responses": __import__("numpy").array([[10, 11]]),
                    "raw_prompt": [[{"role": "user", "content": "query"}]],
                    "extra_info": [{"id": "rl-1", "query": "query"}],
                    "reward_model": [{"ground_truth": "SELECT 1"}],
                    "data_source": ["text2sql"],
                    "extra_fields": [
                        {"reward_extra_info": {"execution_correct": 1.0, "score": 1.2}}
                    ],
                }
            )

            with patch.dict(sys.modules, {"transfer_queue": transfer_queue}):
                result = sampler._evict_terminal_groups(
                    7,
                    "train",
                    (set(), {"abc"}, set(), {1.0: 1}),
                )

            record = json.loads(sft_path.read_text(encoding="utf-8"))

        self.assertEqual(result[2], 1)
        self.assertEqual(record["reason"], "all_correct")
        self.assertEqual(record["candidates"][0]["model_output"], "decoded-11")
        self.assertEqual(record["candidates"][0]["extra_info"]["id"], "rl-1")
        self.assertFalse(bad_path.exists())


if __name__ == "__main__":
    unittest.main()
