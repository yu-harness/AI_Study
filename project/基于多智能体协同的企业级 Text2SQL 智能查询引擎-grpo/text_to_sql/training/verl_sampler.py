"""Bounded veRL V1 replay buffer used by Text2SQL GRPO."""

from __future__ import annotations

import json
from pathlib import Path

from verl.trainer.ppo.v1.replay_buffer import ReplayBuffer


class BoundedReplayBuffer(ReplayBuffer):
    """Use veRL's sync DAPO sampler with a hard total generation budget."""

    def __init__(
        self,
        trainer_mode,
        trainer_config,
        max_off_policy_threshold,
        max_off_policy_strategy,
        sampler_kwargs,
        poll_interval=2.0,
        refill_fn=None,
    ):
        if trainer_mode != "sync":
            raise ValueError("BoundedReplayBuffer supports trainer.v1.trainer_mode=sync only")
        if refill_fn is None:
            raise ValueError("BoundedReplayBuffer requires veRL's refill callback")
        if int(trainer_config.get("parameter_sync_step", 1)) != 1:
            raise ValueError("BoundedReplayBuffer requires sync.parameter_sync_step=1")

        filter_groups_metric = str(sampler_kwargs["filter_groups_metric"])
        if filter_groups_metric != "execution_correct":
            raise ValueError("Text2SQL backflow requires filter_groups_metric=execution_correct")

        self.max_num_gen_batches = int(sampler_kwargs["max_num_gen_batches"])
        self.train_batch_size = int(sampler_kwargs["train_batch_size"])
        if self.max_num_gen_batches <= 0 or self.train_batch_size <= 0:
            raise ValueError("max_num_gen_batches and train_batch_size must be positive integers")

        self._delegate_refill_fn = refill_fn
        self._active_partition = ""
        self._refilled_prompts = 0
        self.tokenizer_path = str(sampler_kwargs["tokenizer_path"])
        self.sft_backflow_path = Path(str(sampler_kwargs["sft_backflow_path"]))
        self.bad_case_backflow_path = Path(str(sampler_kwargs["bad_case_backflow_path"]))
        self._tokenizer = None
        super().__init__(
            trainer_mode=trainer_mode,
            trainer_config=trainer_config,
            max_off_policy_threshold=max_off_policy_threshold,
            max_off_policy_strategy=max_off_policy_strategy,
            sampler_kwargs=sampler_kwargs,
            poll_interval=poll_interval,
            refill_fn=self._bounded_refill,
            filter_groups_metric=filter_groups_metric,
            train_batch_size=self.train_batch_size,
            gen_batch_size=1,
            max_inflight_gen_batches=int(sampler_kwargs["max_inflight_gen_batches"]),
            sync_refill_failed_groups=bool(sampler_kwargs.get("sync_refill_failed_groups", False)),
        )

    def _evict_terminal_groups(self, global_steps, partition_id, eviction_reasons):
        dapo_uids = eviction_reasons[1]
        if partition_id == "train" and dapo_uids:
            self._persist_backflow_groups(global_steps, partition_id, dapo_uids)
        return super()._evict_terminal_groups(global_steps, partition_id, eviction_reasons)

    def _persist_backflow_groups(self, global_steps: int, partition_id: str, uids: set[str]) -> None:
        import transfer_queue as tq

        trajectory_keys = sorted(
            key for key in self.partitions[partition_id] if key.split("_")[0] in uids
        )
        data = tq.kv_batch_get(
            keys=trajectory_keys,
            partition_id=partition_id,
            select_fields=[
                "responses",
                "raw_prompt",
                "extra_info",
                "reward_model",
                "data_source",
                "extra_fields",
            ],
        )
        tokenizer = self._get_tokenizer()
        response_ids = data.select("responses").to_padded_tensor(
            padding=tokenizer.pad_token_id
        )["responses"]
        outputs = tokenizer.batch_decode(response_ids.tolist(), skip_special_tokens=True)
        raw_prompts = _field_values(data, "raw_prompt", len(trajectory_keys))
        extra_infos = _field_values(data, "extra_info", len(trajectory_keys))
        reward_models = _field_values(data, "reward_model", len(trajectory_keys))
        data_sources = _field_values(data, "data_source", len(trajectory_keys))
        extra_fields = _field_values(data, "extra_fields", len(trajectory_keys))

        groups = {}
        for index, key in enumerate(trajectory_keys):
            uid = key.split("_")[0]
            filter_value = self._dapo_classification_cache[partition_id][uid]
            if filter_value not in {0.0, 1.0}:
                raise RuntimeError(f"execution_correct must be binary, got {filter_value}")
            group = groups.setdefault(
                uid,
                {
                    "group_uid": uid,
                    "global_step": int(global_steps),
                    "reason": "all_correct" if filter_value == 1.0 else "all_incorrect",
                    "execution_correct": float(filter_value),
                    "candidates": [],
                },
            )
            reward_extra_info = {}
            if isinstance(extra_fields[index], dict):
                reward_extra_info = extra_fields[index].get("reward_extra_info", {})
            group["candidates"].append(
                {
                    "trajectory_key": key,
                    "model_output": outputs[index],
                    "raw_prompt": raw_prompts[index],
                    "extra_info": extra_infos[index],
                    "reward_model": reward_models[index],
                    "data_source": data_sources[index],
                    "reward_metrics": reward_extra_info,
                }
            )

        for group in groups.values():
            target = self.sft_backflow_path if group["execution_correct"] == 1.0 else self.bad_case_backflow_path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(_jsonable(group), ensure_ascii=False, sort_keys=True))
                stream.write("\n")

    def _get_tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.tokenizer_path,
                local_files_only=True,
            )
        return self._tokenizer

    def _bounded_refill(self, prompt_count: int) -> None:
        if self._active_partition == "train":
            # PPOTrainer submits one full train batch before sample(); only the
            # remaining configured generation batches pass through refill_fn.
            refill_limit = (self.max_num_gen_batches - 1) * self.train_batch_size
            requested_total = self._refilled_prompts + int(prompt_count)
            if requested_total > refill_limit:
                raise RuntimeError(
                    "GRPO group filtering exhausted the refill budget: "
                    f"requested={requested_total}, limit={refill_limit}, "
                    f"max_num_gen_batches={self.max_num_gen_batches}"
                )
        self._delegate_refill_fn(prompt_count)
        if self._active_partition == "train":
            self._refilled_prompts += int(prompt_count)

    def sample(self, global_steps: int, partition_id: str, batch_size: int):
        self._active_partition = partition_id
        self._refilled_prompts = 0
        try:
            return super().sample(global_steps, partition_id, batch_size)
        finally:
            self._active_partition = ""
            self._refilled_prompts = 0


def _field_values(data, field_name: str, size: int) -> list:
    value = data.get(field_name)
    if value is None:
        return [None] * size
    if hasattr(value, "tolist"):
        value = value.tolist()
    return list(value)


def _jsonable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        return _jsonable(value.item())
    if hasattr(value, "tolist"):
        return _jsonable(value.tolist())
    return str(value)
