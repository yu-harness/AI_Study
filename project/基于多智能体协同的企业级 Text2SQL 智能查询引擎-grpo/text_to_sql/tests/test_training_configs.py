import json
import tempfile
import unittest
from pathlib import Path

from text_to_sql.training.configs import (
    build_deepspeed_zero2_optimizer_offload_config,
    build_dpo_config,
    build_grpo_config,
    build_lora_merge_config,
    build_sft_config,
    init_training_artifacts,
)


class TestTrainingConfigs(unittest.TestCase):
    def test_sft_config_matches_design_stage(self):
        config = build_sft_config()

        self.assertEqual(config["stage"], "sft")
        self.assertEqual(config["cutoff_len"], 8192)
        self.assertEqual(config["deepspeed"], "deepspeed/ds_z2_config.json")
        self.assertFalse(config["train_on_prompt"])
        self.assertNotIn("train_on_inputs", config)
        self.assertTrue(config["do_eval"])
        self.assertEqual(config["val_size"], 0.1)

    def test_dpo_config_uses_preference_loss(self):
        config = build_dpo_config(
            model_name_or_path="models/sft_merged",
        )

        self.assertEqual(config["stage"], "dpo")
        self.assertEqual(config["model_name_or_path"], "models/sft_merged")
        self.assertNotIn("adapter_name_or_path", config)
        self.assertEqual(config["pref_loss"], "sigmoid")
        self.assertEqual(config["lora_rank"], 64)
        self.assertEqual(config["lora_alpha"], 32)
        self.assertTrue(config["create_new_adapter"])
        self.assertEqual(config["per_device_train_batch_size"], 1)
        self.assertEqual(
            config["deepspeed"],
            "deepspeed/ds_z2_optimizer_offload_config.json",
        )
        self.assertEqual(config["val_size"], 0.1)

    def test_grpo_config_wires_reward_functions(self):
        config = build_grpo_config(model_name_or_path="models/dpo_merged")

        self.assertEqual(config["defaults"], ["ppo_trainer", "_self_"])
        self.assertEqual(config["actor_rollout_ref"]["model"]["path"], "models/dpo_merged")
        self.assertEqual(config["actor_rollout_ref"]["rollout"]["name"], "vllm")
        self.assertEqual(config["actor_rollout_ref"]["rollout"]["n"], 4)
        self.assertEqual(config["algorithm"]["adv_estimator"], "grpo")
        self.assertTrue(config["algorithm"]["filter_groups"]["enable"])
        self.assertEqual(
            config["algorithm"]["filter_groups"]["metric"],
            "execution_correct",
        )
        self.assertEqual(config["trainer"]["total_training_steps"], 2500)
        self.assertGreaterEqual(config["trainer"]["total_epochs"], 20)
        self.assertTrue(config["trainer"]["use_v1"])
        sampler = config["trainer"]["v1"]["sampler"]
        self.assertEqual(
            sampler["custom_sampler"],
            {
                "path": "${oc.env:TEXT2SQL_REPLAY_BUFFER_PATH}",
                "name": "BoundedReplayBuffer",
            },
        )
        self.assertEqual(
            sampler["sampler_kwargs"]["max_num_gen_batches"],
            "${algorithm.filter_groups.max_num_gen_batches}",
        )
        self.assertEqual(
            sampler["sampler_kwargs"]["sft_backflow_path"],
            "${oc.env:TEXT2SQL_SFT_BACKFLOW_PATH}",
        )
        self.assertEqual(
            sampler["sampler_kwargs"]["bad_case_backflow_path"],
            "${oc.env:TEXT2SQL_BAD_CASE_BACKFLOW_PATH}",
        )
        self.assertEqual(
            config["reward"]["custom_reward_function"]["name"],
            "compute_score",
        )
        self.assertEqual(
            config["reward"]["custom_reward_function"]["reward_kwargs"]["judge_model"],
            "qwen3.5:4b",
        )
        self.assertIn(
            "sandbox_db_urls",
            config["reward"]["custom_reward_function"]["reward_kwargs"],
        )

    def test_lora_merge_config_materializes_dpo_adapter(self):
        config = build_lora_merge_config(
            model_name_or_path="Qwen/Qwen2.5-Coder-14B",
            adapter_name_or_path="models/dpo",
            export_dir="models/dpo_merged",
        )

        self.assertEqual(config["adapter_name_or_path"], "models/dpo")
        self.assertEqual(config["export_dir"], "models/dpo_merged")
        self.assertEqual(config["export_device"], "auto")
        self.assertFalse(config["export_legacy_format"])

    def test_dpo_deepspeed_config_offloads_optimizer(self):
        config = build_deepspeed_zero2_optimizer_offload_config()

        self.assertEqual(config["zero_optimization"]["stage"], 2)
        self.assertEqual(
            config["zero_optimization"]["offload_optimizer"]["device"],
            "cpu",
        )

    def test_init_training_artifacts_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = init_training_artifacts(tmp, sft_checkpoint="models/sft")
            for path in paths.values():
                self.assertTrue(Path(path).exists())
            with Path(paths["dataset_info"]).open("r", encoding="utf-8") as f:
                dataset_info = json.load(f)
            sft_dpo_requirements = Path(paths["sft_dpo_requirements"]).read_text(
                encoding="utf-8"
            )
            grpo_requirements = Path(paths["grpo_requirements"]).read_text(
                encoding="utf-8"
            )
            environments = Path(paths["training_environments"]).read_text(
                encoding="utf-8"
            )

        self.assertIn("text2sql_sft_cot", dataset_info)
        self.assertIn("text2sql_dpo_aligned", dataset_info)
        self.assertIn("llamafactory==0.9.5", sft_dpo_requirements)
        self.assertNotIn("verl", sft_dpo_requirements.lower())
        self.assertIn("oracledb==4.0.2", grpo_requirements)
        self.assertIn("greenlet==3.5.5", grpo_requirements)
        self.assertIn("prometheus-client==0.25.0", grpo_requirements)
        self.assertNotIn("llamafactory", grpo_requirements.lower())
        self.assertIn("fc6ca747eb20aaf5ff8fc5e805468790292c79f7", environments)
        self.assertIn("--frozen", environments)
        self.assertIn("--no-deps", environments)
        self.assertIn("uv pip check", environments)

    def test_init_training_artifacts_deepspeed_path_matches_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = init_training_artifacts(tmp, sft_checkpoint="models/sft")
            expected = Path(tmp) / build_sft_config()["deepspeed"]

        self.assertEqual(Path(paths["deepspeed_config"]), expected)

    def test_init_training_artifacts_wires_all_model_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = init_training_artifacts(
                tmp,
                sft_model="Qwen/Qwen2.5-Coder-14B",
                sft_checkpoint="models/sft",
                merged_sft_model="models/sft_merged",
                dpo_checkpoint="models/dpo",
                merged_dpo_model="models/dpo_merged",
            )
            import yaml

            with Path(paths["sft_config"]).open("r", encoding="utf-8") as f:
                sft_config = yaml.safe_load(f)
            with Path(paths["merge_sft_config"]).open("r", encoding="utf-8") as f:
                merge_sft_config = yaml.safe_load(f)
            with Path(paths["dpo_config"]).open("r", encoding="utf-8") as f:
                dpo_config = yaml.safe_load(f)
            with Path(paths["merge_dpo_config"]).open("r", encoding="utf-8") as f:
                merge_dpo_config = yaml.safe_load(f)
            with Path(paths["grpo_config"]).open("r", encoding="utf-8") as f:
                grpo_config = yaml.safe_load(f)

        self.assertEqual(sft_config["model_name_or_path"], "Qwen/Qwen2.5-Coder-14B")
        self.assertEqual(sft_config["output_dir"], "models/sft")
        self.assertEqual(merge_sft_config["model_name_or_path"], "Qwen/Qwen2.5-Coder-14B")
        self.assertEqual(merge_sft_config["adapter_name_or_path"], "models/sft")
        self.assertEqual(merge_sft_config["export_dir"], "models/sft_merged")
        self.assertEqual(dpo_config["model_name_or_path"], "models/sft_merged")
        self.assertEqual(dpo_config["output_dir"], "models/dpo")
        self.assertNotIn("adapter_name_or_path", dpo_config)
        self.assertEqual(merge_dpo_config["model_name_or_path"], "models/sft_merged")
        self.assertEqual(merge_dpo_config["adapter_name_or_path"], "models/dpo")
        self.assertEqual(merge_dpo_config["export_dir"], "models/dpo_merged")
        self.assertEqual(grpo_config["actor_rollout_ref"]["model"]["path"], "models/dpo_merged")


if __name__ == "__main__":
    unittest.main()
