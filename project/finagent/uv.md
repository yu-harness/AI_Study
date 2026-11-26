# uv 速览

一句话：uv = pip + virtualenv + pyenv + pip-tools 的合体，Rust 写的单文件工具。本项目用它装依赖、锁版本、跑脚本、管 Python 版本。

本机实测：`uv 0.12.23`，项目 `.venv` 里是 `Python 3.13.14`，锁文件锁定 62 个包。

## 三个文件的关系

```
pyproject.toml   声明「我要什么范围」       fastapi>=0.115
   ↓ uv lock
uv.lock          记录「实际是哪 62 个版本」 每包 version + url + sha256
   ↓ uv sync
.venv/           落到磁盘的真实环境
```

声明用范围，复现用锁，落地用同步。三者职责不重叠，别手动改 `uv.lock`。

## 必须会的命令

| 命令 | 作用 | 本项目场景 |
| --- | --- | --- |
| `uv sync` | 按 lock 精确安装，环境与 lock 对齐 | 拉下代码第一步 |
| `uv sync --extra dev` | 额外装 `optional-dependencies.dev` | 跑测试前 |
| `uv add <pkg>` | 加依赖，自动改 pyproject + relock + 安装 | 新增库 |
| `uv add --dev <pkg>` | 加到 dev 组 | 装 lint/测试工具 |
| `uv remove <pkg>` | 删依赖并重锁 | 清理 |
| `uv run <cmd>` | 在项目环境里执行命令，先自动同步 | 跑服务/测试 |
| `uv lock` | 只重算 lock，不动环境 | 手改 pyproject 后 |
| `uv lock --check` | 校验 lock 是否过期，CI 用 | 提交前检查 |
| `uv tree` | 打印依赖树，排查谁引入了某包 | 查冲突 |
| `uv python pin 3.13` | 固定解释器版本（写 `.python-version`） | 统一团队版本 |
| `uv python install 3.12` | 下载并托管一个解释器 | 机器上没有该版本时 |

本项目实际跑法（入口以 README 为准）：

```powershell
uv sync --extra dev
uv run python -m finagent.scripts.init_db
uv run python -m finagent.scripts.run_api          # 127.0.0.1:8000
uv run python -m pytest finagent/tests -q
```

## 和 pip 的心智差异

1. **不用 activate**。`uv run` 会先确保 `.venv` 与 lock 一致，再把 `.venv` 注入 PATH 执行命令。手敲 `activate` 属于 pip 时代的习惯。
2. **全局缓存 + 硬链接**。包只下载一次、只存一份，多个项目共享；删环境不删缓存，所以重装是秒级。
3. **增量解析**。只重算受影响的子树，不全量重解，所以改一个依赖不会等半分钟。
4. **解析在前、安装在后的分离**。`uv lock` 只算不装，适合 CI 先校验再装。
5. **`uv pip ...` 是兼容壳**。`uv pip install` / `uv pip freeze` 模仿 pip 行为，绕开项目模式，用来对付老脚本；日常别混着用。

## 容易踩的点

- `uv sync` 默认会**顺手改 lock**；只在安装、不许改动用 `uv sync --frozen`，要求 lock 必须最新否则报错用 `--locked`。
- `requires-python = ">=3.11"` 是解析约束，不是"会帮你装 3.11"；解释器得 `uv python install` / `uv python pin` 显式管。
- 生产环境靠 `--extra production` 拉起 neo4j / psycopg / pymilvus / temporalio，漏了这层会出现"本地能跑、线上 import 失败"。
- 生成的包名带连字符、导入名不带（`psycopg[binary]` → `import psycopg`）。

## 面试一句话版

> uv 用 Rust 重写了依赖解析与安装链路，靠全局缓存加硬链接把重复安装变成文件链接，配合 lock 文件做到「声明范围、锁定精确、环境可复现」，同时把解释器管理和脚本执行收进一个二进制，所以 pip + virtualenv + pyenv 那一套被一个 `uv sync` / `uv run` 取代。
