"""Training configuration templates from the Text2SQL design document."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def build_sft_config(
    model_name_or_path: str = "Qwen/Qwen2.5-Coder-14B",
    dataset: str = "text2sql_sft_cot",
    output_dir: str = "models/sft_qwen2.5_coder_14b",
    deepspeed: str = "deepspeed/ds_z2_config.json",
) -> dict:
    """Return the LlamaFactory SFT config described in appendix A.1."""

    return {
        "model_name_or_path": model_name_or_path,
        "stage": "sft",
        "do_train": True,
        "finetuning_type": "lora",
        "lora_target": "all",
        "lora_rank": 64,
        "lora_alpha": 32,
        "dataset": dataset,
        "dataset_dir": "data",
        "template": "qwen",
        "cutoff_len": 8192,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "learning_rate": 1.0e-5,
        "num_train_epochs": 3.0,
        "bf16": True,
        "flash_attn": "fa2",
        "deepspeed": deepspeed,
        "train_on_prompt": False,
        "gradient_checkpointing": True,
        "max_grad_norm": 0.5,
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.03,
        "logging_steps": 10,
        "save_steps": 500,
        "plot_loss": True,
        "overwrite_cache": True,
        "preprocessing_num_workers": 8,
        # The admission gate requires enough source rows to leave 70K training
        # samples after LlamaFactory reserves this validation split.
        "val_size": 0.1,
        "do_eval": True,
        "eval_strategy": "steps",
        "eval_steps": 500,
        "output_dir": output_dir,
    }


def build_dpo_config(
    model_name_or_path: str = "models/sft_qwen2.5_coder_14b_merged",
    dataset: str = "text2sql_dpo_aligned",
    output_dir: str = "models/dpo_qwen2.5_coder_14b",
    deepspeed: str = "deepspeed/ds_z2_optimizer_offload_config.json",
) -> dict:
    """Return the LlamaFactory DPO config described in appendix A.2."""

    return {
        "model_name_or_path": model_name_or_path,
        "stage": "dpo",
        "do_train": True,
        "finetuning_type": "lora",
        "lora_target": "all",
        "lora_rank": 64,
        "lora_alpha": 32,
        "create_new_adapter": True,
        "dataset": dataset,
        "dataset_dir": "data",
        "template": "qwen",
        "cutoff_len": 8192,
        "pref_beta": 0.1,
        "pref_loss": "sigmoid",
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "learning_rate": 5.0e-7,
        "num_train_epochs": 1.0,
        "bf16": True,
        "flash_attn": "fa2",
        "deepspeed": deepspeed,
        "gradient_checkpointing": True,
        "max_grad_norm": 0.5,
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.03,
        "logging_steps": 10,
        "save_steps": 500,
        "plot_loss": True,
        "overwrite_cache": True,
        "preprocessing_num_workers": 8,
        # The admission gate requires enough source rows to leave 20K training
        # pairs after LlamaFactory reserves this validation split.
        "val_size": 0.1,
        "do_eval": True,
        "eval_strategy": "steps",
        "eval_steps": 500,
        "output_dir": output_dir,
    }


def build_grpo_config(
    model_name_or_path: str = "models/dpo_qwen2.5_coder_14b_merged",
    train_files: str = "data/text2sql_rl_train.parquet",
    val_files: str = "data/text2sql_rl_valid.parquet",
) -> dict:
    """Return a veRL Hydra override config for the documented GRPO stage."""

    return {
        "hydra": {
            "searchpath": ["pkg://verl.trainer.config"],
        },
        "defaults": ["ppo_trainer", "_self_"],
        "data": {
            "train_files": train_files,
            "val_files": val_files,
            "prompt_key": "prompt",
            "reward_fn_key": "data_source",
            "train_batch_size": 64,
            "max_prompt_length": 6144,
            "max_response_length": 2048,
            "filter_overlong_prompts": True,
            "truncation": "error",
            "return_raw_chat": True,
        },
        "actor_rollout_ref": {
            "model": {
                "path": model_name_or_path,
                "enable_gradient_checkpointing": True,
                "use_remove_padding": True,
            },
            "actor": {
                "strategy": "fsdp",
                "optim": {
                    "lr": 1.0e-6,
                    "weight_decay": 0.01,
                },
                "ppo_mini_batch_size": 64,
                "ppo_micro_batch_size_per_gpu": 1,
                "use_kl_loss": True,
                "kl_loss_coef": 0.05,
                "kl_loss_type": "low_var_kl",
                "entropy_coeff": 0.0,
                "fsdp_config": {
                    "param_offload": False,
                    "optimizer_offload": False,
                },
            },
            "rollout": {
                "name": "vllm",
                "temperature": 0.7,
                "top_p": 0.9,
                "n": 4,
                "enable_prefix_caching": True,
                "tensor_model_parallel_size": 1,
                "gpu_memory_utilization": 0.5,
                "log_prob_micro_batch_size_per_gpu": 1,
            },
            "ref": {
                "log_prob_micro_batch_size_per_gpu": 1,
                "fsdp_config": {
                    "param_offload": True,
                },
            },
        },
        "algorithm": {
            "adv_estimator": "grpo",
            "use_kl_in_reward": False,
            "filter_groups": {
                "enable": True,
                "metric": "execution_correct",
                "max_num_gen_batches": 10,
                "max_inflight_gen_batches": 10,
            },
        },
        "reward": {
            "custom_reward_function": {
                "path": "${oc.env:TEXT2SQL_REWARD_PATH}",
                "name": "compute_score",
                "reward_kwargs": {
                    "sandbox_db_urls": "${oc.env:TEXT2SQL_TRAINING_DB_URLS}",
                    "redis_url": "${oc.env:TEXT2SQL_REDIS_URL}",
                    "judge_base_url": "${oc.env:TEXT2SQL_JUDGE_BASE_URL,http://127.0.0.1:8000}",
                    "judge_model": "qwen3.5:4b",
                    "tokenizer_path": "${actor_rollout_ref.model.path}",
                },
            },
        },
        "trainer": {
            "use_v1": True,
            "v1": {
                "trainer_mode": "sync",
                "sampler": {
                    "custom_sampler": {
                        "path": "${oc.env:TEXT2SQL_REPLAY_BUFFER_PATH}",
                        "name": "BoundedReplayBuffer",
                    },
                    "sampler_kwargs": {
                        "filter_groups_metric": "${algorithm.filter_groups.metric}",
                        "max_num_gen_batches": "${algorithm.filter_groups.max_num_gen_batches}",
                        "max_inflight_gen_batches": (
                            "${algorithm.filter_groups.max_inflight_gen_batches}"
                        ),
                        "train_batch_size": "${data.train_batch_size}",
                        "sync_refill_failed_groups": False,
                        "tokenizer_path": "${actor_rollout_ref.model.path}",
                        "sft_backflow_path": "${oc.env:TEXT2SQL_SFT_BACKFLOW_PATH}",
                        "bad_case_backflow_path": "${oc.env:TEXT2SQL_BAD_CASE_BACKFLOW_PATH}",
                    },
                },
            },
            "critic_warmup": 0,
            "logger": ["console", "wandb"],
            "project_name": "text2sql-grpo",
            "experiment_name": "qwen2.5-coder-14b",
            "n_gpus_per_node": 8,
            "nnodes": 1,
            "save_freq": 100,
            "test_freq": 50,
            # veRL V1 stops when either the epoch or explicit step bound is hit.
            # Keep the fixed upstream default high enough for 2,500 steps over
            # the documented 8K/64 = 125-step training epoch.
            "total_epochs": 30,
            "total_training_steps": 2500,
            "default_local_dir": "models/grpo_qwen2.5_coder_14b",
        },
    }


def build_lora_merge_config(
    model_name_or_path: str = "Qwen/Qwen2.5-Coder-14B",
    adapter_name_or_path: str = "models/dpo_qwen2.5_coder_14b",
    export_dir: str = "models/dpo_qwen2.5_coder_14b_merged",
) -> dict:
    """Return a LlamaFactory config that materializes a LoRA adapter."""

    return {
        "model_name_or_path": model_name_or_path,
        "adapter_name_or_path": adapter_name_or_path,
        "template": "qwen",
        "finetuning_type": "lora",
        "export_dir": export_dir,
        "export_size": 5,
        "export_device": "auto",
        "export_legacy_format": False,
    }


def build_deepspeed_zero2_config() -> dict:
    """Return a conservative DeepSpeed ZeRO-2 config for 8xA100 training."""

    return {
        "train_batch_size": "auto",
        "train_micro_batch_size_per_gpu": "auto",
        "gradient_accumulation_steps": "auto",
        "gradient_clipping": 0.5,
        "zero_optimization": {
            "stage": 2,
            "allgather_partitions": True,
            "allgather_bucket_size": 2e8,
            "overlap_comm": True,
            "reduce_scatter": True,
            "reduce_bucket_size": 2e8,
            "contiguous_gradients": True,
        },
        "bf16": {
            "enabled": "auto",
        },
        "fp16": {
            "enabled": False,
        },
        "activation_checkpointing": {
            "partition_activations": False,
            "cpu_checkpointing": False,
            "contiguous_memory_optimization": False,
        },
        "wall_clock_breakdown": False,
    }


def build_deepspeed_zero2_optimizer_offload_config() -> dict:
    """Return ZeRO-2 with CPU optimizer offload for the DPO stage."""

    config = build_deepspeed_zero2_config()
    config["zero_optimization"]["offload_optimizer"] = {
        "device": "cpu",
        "pin_memory": True,
    }
    return config


def build_dataset_info() -> dict:
    """Return LlamaFactory dataset_info entries for SFT and DPO files."""

    return {
        "text2sql_sft_cot": {
            "file_name": "text2sql_sft_cot.jsonl",
            "formatting": "alpaca",
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "response": "output",
                "history": "history",
            },
        },
        "text2sql_dpo_aligned": {
            "file_name": "text2sql_dpo_aligned.jsonl",
            "ranking": True,
            "formatting": "alpaca",
            "columns": {
                "prompt": "instruction",
                "query": "input",
                "chosen": "chosen",
                "rejected": "rejected",
                "history": "history",
            },
        },
    }


def init_training_artifacts(
    output_dir: str | Path,
    sft_model: str = "Qwen/Qwen2.5-Coder-14B",
    sft_checkpoint: str = "models/sft_qwen2.5_coder_14b",
    merged_sft_model: str = "models/sft_qwen2.5_coder_14b_merged",
    dpo_checkpoint: str = "models/dpo_qwen2.5_coder_14b",
    merged_dpo_model: str = "models/dpo_qwen2.5_coder_14b_merged",
) -> dict[str, str]:
    """Create the local config skeleton needed by the offline training cluster."""

    root = Path(output_dir)
    config_dir = root / "configs"
    data_dir = root / "data"
    deepspeed_dir = root / "deepspeed"
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    deepspeed_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "sft_config": config_dir / "sft_qwen.yaml",
        "merge_sft_config": config_dir / "merge_sft_qwen.yaml",
        "dpo_config": config_dir / "dpo_qwen.yaml",
        "merge_dpo_config": config_dir / "merge_dpo_qwen.yaml",
        "grpo_config": config_dir / "grpo_text2sql.yaml",
        "deepspeed_config": deepspeed_dir / "ds_z2_config.json",
        "deepspeed_optimizer_offload_config": (
            deepspeed_dir / "ds_z2_optimizer_offload_config.json"
        ),
        "dataset_info": data_dir / "dataset_info.json",
        "sft_dpo_requirements": root / "requirements-sft-dpo.txt",
        "grpo_requirements": root / "requirements-grpo.txt",
        "training_environments": root / "TRAINING_ENVIRONMENTS.md",
    }

    _write_yaml(
        paths["sft_config"],
        build_sft_config(
            model_name_or_path=sft_model,
            output_dir=sft_checkpoint,
        ),
    )
    _write_yaml(
        paths["merge_sft_config"],
        build_lora_merge_config(
            model_name_or_path=sft_model,
            adapter_name_or_path=sft_checkpoint,
            export_dir=merged_sft_model,
        ),
    )
    _write_yaml(
        paths["dpo_config"],
        build_dpo_config(
            model_name_or_path=merged_sft_model,
            output_dir=dpo_checkpoint,
        ),
    )
    _write_yaml(
        paths["merge_dpo_config"],
        build_lora_merge_config(
            model_name_or_path=merged_sft_model,
            adapter_name_or_path=dpo_checkpoint,
            export_dir=merged_dpo_model,
        ),
    )
    _write_yaml(
        paths["grpo_config"],
        build_grpo_config(model_name_or_path=merged_dpo_model),
    )
    _write_json(paths["deepspeed_config"], build_deepspeed_zero2_config())
    _write_json(
        paths["deepspeed_optimizer_offload_config"],
        build_deepspeed_zero2_optimizer_offload_config(),
    )
    _write_json(paths["dataset_info"], build_dataset_info())
    for artifact_name, source_name in (
        ("sft_dpo_requirements", "requirements-sft-dpo.txt"),
        ("grpo_requirements", "requirements-grpo.txt"),
        ("training_environments", "TRAINING_ENVIRONMENTS.md"),
    ):
        source = Path(__file__).with_name(source_name)
        paths[artifact_name].write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    return {name: str(path) for name, path in paths.items()}


def _write_yaml(path: str | Path, data: MappingLike) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _write_json(path: str | Path, data: MappingLike) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


MappingLike = dict[str, Any]
