# 独立训练环境

SFT/DPO 与 GRPO 必须使用两个独立的 Linux Python 3.12 环境。LlamaFactory
0.9.5 与固定 veRL 提交使用的 TRL/PyTorch 栈不同，禁止把两个 requirements
文件安装进同一个虚拟环境。

## SFT / DPO

```bash
python3.12 -m venv .venv-sft-dpo
source .venv-sft-dpo/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.8.0
python -m pip install packaging==25.0 ninja==1.13.0
python -m pip install --no-build-isolation -r requirements-sft-dpo.txt
```

`flash-attn` 编译必须在目标 A100/CUDA 节点完成，不能复用本地 Windows
构建产物。DPO 的 LoRA reference 由 LlamaFactory 通过暂时禁用同一模型的
Adapter 计算；DeepSpeed 配置中的 CPU Offload 对象是 optimizer state，不是
第二份 reference 参数。

## GRPO

GRPO 使用 veRL 固定提交自带的 `uv.lock` 锁定 vLLM、FSDP、PyTorch、CUDA
和 TransferQueue。项目依赖作为精确版本 overlay 以 `--no-deps` 安装，禁止
重新解析或升级 veRL 锁中的依赖；安装后必须通过 `uv pip check`。

```bash
git clone https://github.com/verl-project/verl.git verl-fc6ca747
cd verl-fc6ca747
git checkout fc6ca747eb20aaf5ff8fc5e805468790292c79f7
uv sync --extra vllm --extra fsdp --frozen
uv pip install --python .venv/bin/python --no-deps -r /absolute/path/requirements-grpo.txt
uv pip check --python .venv/bin/python
```

`requirements-grpo.txt` 中与上游重复的 `pyarrow`、`prometheus-client` 版本
必须和该提交的 `uv.lock` 完全一致；SQLAlchemy 在 Linux CPython 上需要的
`greenlet` 也在 overlay 中显式固定，最终环境不会发生隐式依赖解析。

随后在该 `.venv` 中执行 `python -m verl.trainer.main_ppo`。项目根目录必须在
`PYTHONPATH`，并设置初始化命令输出的 Reward、ReplayBuffer、SFT/Bad Case
回流池和沙箱环境变量。两个回流路径必须指向训练节点上的持久化目录。
