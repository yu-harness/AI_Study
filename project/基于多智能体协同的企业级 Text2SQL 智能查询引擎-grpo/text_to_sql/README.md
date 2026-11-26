# Text2SQL

基于 LLM 的智能自然语言转 SQL 系统，支持多轮修复、语义检索、沙箱执行一致性校验。

## 架构概览

```
用户查询（自然语言）
    │
    ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐
│  Router  │───▶│ Planner  │───▶│  Coder   │───▶│ Executor  │
│ 数据库路由 │    │ 查询规划  │    │ SQL生成   │    │ 沙箱执行   │
└──────────┘    └──────────┘    └──────────┘    └───────────┘
                     │                                │
                     │ 检索增强                         │ 一致性选择
                     ▼                                ▼
              ┌─────────────┐              ┌───────────────────┐
              │ Schema/业务  │             │ ConsistencySelector│
              │ KB/实体链接  │              │   (Judge LLM)     │
              └─────────────┘              └───────────────────┘
```

## 功能特性

- **多 Agent 工作流** — Router → Planner → Coder → Executor，支持自动重试修复
- **检索增强 (RAG)** — 自动检索相关表结构、业务知识、值映射，注入 LLM 上下文
- **多候选 SQL 生成** — Coder 节点一次生成多个 SQL 候选，Executor 在沙箱中执行并选优
- **一致性选择器** — 可选 Judge LLM 对候选 SQL 结果进行语义一致性校验
- **语义缓存** — 基于 embedding 相似度的查询缓存，避免重复计算
- **沙箱安全执行** — SQL 在受限沙箱数据库执行，默认单表扫描上限 1000 万行
- **数据库方言路由** — 支持多数据库路由，自动匹配 SQL 方言规则
- **元数据自动采集** — 定时同步数据库 schema，支持表/列级分词索引
- **离线训练工具** — 生成 SFT/DPO/GRPO 配置，校验训练样本，计算 GRPO reward
- **Web UI + API** — 内置 FastAPI 服务和前端页面，开箱即用

## 快速开始

### 环境要求

- Python 3.10+
- Docker Desktop
- Ollama 兼容服务：`http://127.0.0.1:8000`
- 本地模型：`qwen3.5:4b`（Agent）和 `bge-m3:latest`（语义检索）
- Redis 7、Elasticsearch 8.11（含 IK 分词插件）、PostgreSQL 16

### 安装

```bash
cd text_to_sql
pip install -r requirements.txt

# 可选：安装 langgraph 以获得完整工作流支持
pip install langgraph
```

确认本地模型服务已经提供两个模型；缺失时先拉取：

```bash
ollama pull qwen3.5:4b
ollama pull bge-m3:latest
curl http://127.0.0.1:8000/api/tags
```

### 配置

编辑 `text_to_sql/config.yaml`，主要调整：

```yaml
llm:
  planner:
    model: "qwen3.5:4b"           # 本地 Agent 模型
    base_url: "http://127.0.0.1:8000"  # Ollama 地址
embedding:
  provider: "ollama"
  model: "bge-m3:latest"
  base_url: "http://127.0.0.1:8000"
database:
  targets:
    docker_postgres:
      url: "postgresql+psycopg2://text2sql_readonly:text2sql_readonly@127.0.0.1:55432/text2sql"
      metadata_url: "postgresql+psycopg2://text2sql_readonly:text2sql_readonly@127.0.0.1:55432/text2sql"
    local_sqlite:
      url: "sqlite:///./data/sandbox.sqlite"
      metadata_url: "sqlite:///./data/sandbox.sqlite"
  cache:
    redis_url: "redis://127.0.0.1:6379/0"
elasticsearch:
  hosts: ["http://127.0.0.1:9200"]
  analyzer: "ik_max_word"
```

`database.targets` 可配置多个目标库。Router 选出的 `target_db` 会同时决定 Schema 索引、连接池、Executor 和语义缓存命名空间；`docker_postgres` 使用只读账号，`local_sqlite` 会解析为 SQLite 只读 URI，并强制 `PRAGMA query_only=ON`。查询中明确写出“SQLite”“本地演示库”或“sandbox.sqlite”可路由到本地库。

### 启动

在仓库根目录执行：

```bash
# 1. 启动真实 Redis、Elasticsearch 和 PostgreSQL 沙箱
docker compose -f text_to_sql/docker-compose.dev.yml up -d --build redis elasticsearch sandbox-db

# 2. 初始化演示表与数据
python -m text_to_sql.runtime.seed_sandbox_data \
  --db-url postgresql+psycopg2://text2sql:text2sql@127.0.0.1:55432/text2sql \
  --reset

# 3a. CLI 单次查询
python -m text_to_sql.main --config text_to_sql/config.runtime.yaml --query "查询所有用户订单金额"

# 3b. 或启动 API 服务（8000 已由 Ollama 使用）
TEXT2SQL_CONFIG=text_to_sql/config.runtime.yaml \
  uvicorn text_to_sql.main:app_api --host 127.0.0.1 --port 8011
```

PowerShell 启动 API 时，先执行 `$env:TEXT2SQL_CONFIG="text_to_sql/config.runtime.yaml"`，再执行 `uvicorn text_to_sql.main:app_api --host 127.0.0.1 --port 8011`。

如果沿用了旧版 PostgreSQL 命名卷，在 `docker compose up -d` 后执行一次下面的幂等权限脚本：

```bash
docker exec text2sql-sandbox-db psql -U text2sql -d text2sql \
  -f /docker-entrypoint-initdb.d/001-readonly.sql
```

访问 `http://127.0.0.1:8011` 查看 Web 界面。严格模式不会回退到内存 Redis、内存实体索引或替代 embedding；任一必需服务不可用时，应用启动会直接失败。

若希望 API 也运行在 Docker 中，停止占用宿主机 8011 端口的进程后执行：

```bash
docker compose -f text_to_sql/docker-compose.dev.yml up -d --build
```

Prometheus 指标地址为 `http://127.0.0.1:9090`，应用原始指标为 `/metrics`。

### API

```bash
# 健康检查
curl http://127.0.0.1:8011/health

# 就绪检查（验证全部数据库、Redis、Elasticsearch、Ollama 和必需模型）
curl http://127.0.0.1:8011/ready

# 自然语言转 SQL
curl -X POST http://127.0.0.1:8011/query \
  -H "Content-Type: application/json" \
  -d '{"query": "上月销售额最高的三个产品"}'

# 明确查询只读 SQLite 数据源
curl -X POST http://127.0.0.1:8011/query \
  -H "Content-Type: application/json" \
  -d '{"query": "在 SQLite 本地演示库查询前 3 个用户"}'
```

响应格式：

```json
{
  "sql": "SELECT p.name, SUM(oi.amount) AS total ...",
  "success": true,
  "cached": false,
  "fallback": false,
  "target_db": "docker_postgres",
  "dialect": "postgresql",
  "data": [...],
  "row_count": 3,
  "trace_id": "abc123",
  "retry_count": 0,
  "debug_trace": [...]
}
```

### Kubernetes 模型灰度与回滚

`k8s/text2sql.yaml` 提供 Nginx Ingress，`k8s/text2sql-canary.yaml` 使用独立 Deployment/Service 和相同 host/path 接收 10% 流量。脚本默认模型仍为 `qwen3.5:4b`，模型历史在稳定 Deployment 注解中只保留最近 3 个版本：

```powershell
./text_to_sql/scripts/rollout-model.ps1 -Action Canary -Model qwen3.5:4b
./text_to_sql/scripts/rollout-model.ps1 -Action Promote -Model qwen3.5:4b
./text_to_sql/scripts/rollout-model.ps1 -Action Rollback
```

## 项目结构

```
text_to_sql/
├── main.py                  # 系统入口：Text2SQLSystem + FastAPI
├── config.yaml              # 主配置文件
├── config.runtime.yaml      # 本机严格运行配置
├── config.docker.yaml       # Docker Compose 运行配置
├── config.k8s.yaml          # Kubernetes 运行配置
├── docker-compose.dev.yml   # API/Redis/ES/PostgreSQL/Prometheus
├── Dockerfile               # API 镜像
├── docker/postgres/         # PostgreSQL 只读应用账号初始化
├── requirements.txt         # 依赖
├── agents/                  # LLM Agent 工作流
│   ├── workflow.py          # LangGraph 工作流定义
│   ├── state.py             # 状态定义
│   ├── planner_node.py      # 查询规划节点
│   ├── coder_node.py        # SQL 生成节点（多候选）
│   ├── executor_node.py     # 沙箱执行 + 一致性选择
│   ├── consistency_selector.py  # Judge LLM 一致性校验
│   ├── prompts.py           # Prompt 模板
│   ├── fallback.py          # 兜底恢复策略
│   ├── sql_utils.py         # SQL 提取与校验
│   └── debug_trace.py       # 调试追踪
├── retrieval/               # RAG 检索增强
│   ├── schema_retriever.py  # 表/列结构检索（BM25 + embedding）
│   ├── business_kb.py       # 业务知识库检索
│   ├── entity_linker.py     # 实体值映射链接
│   ├── embeddings.py        # Embedding 模型工厂
│   └── router.py            # 数据库语义路由
├── sandbox/                 # SQL 安全执行
│   ├── connection_pool.py   # 数据库连接池
│   ├── executor.py          # 沙箱执行器（限行/限时/限表）
│   └── security.py          # SQL 安全校验
├── llm/                     # LLM 客户端
│   └── ollama_client.py     # Ollama 客户端封装
├── metadata/                # 数据库元数据管理
│   ├── collector.py         # Schema 采集器
│   └── scheduler.py         # 定时刷新调度器
├── cache/
│   └── semantic_cache.py    # 语义缓存（embedding 相似度匹配）
├── runtime/
│   ├── seed_sandbox_data.py # 测试数据填充
│   └── stress_test.py       # 有界 HTTP 并发压力测试
├── training/                # 离线训练配置、数据校验和 GRPO reward
│   ├── configs.py           # LlamaFactory/DeepSpeed/veRL 配置模板
│   ├── data.py              # SFT/DPO/GRPO 数据格式与质检
│   ├── rewards.py           # 沙盒执行、格式和 Judge reward 组合
│   ├── sandbox_routes.py    # 训练库级路由与沙盒执行器构造
│   ├── verl_sampler.py      # veRL V1 有界 ReplayBuffer
│   ├── requirements-sft-dpo.txt # LlamaFactory GPU 环境
│   ├── requirements-grpo.txt    # veRL 冻结环境的项目依赖
│   ├── TRAINING_ENVIRONMENTS.md # 两套独立训练环境安装契约
│   └── cli.py               # python -m text_to_sql.training
├── configs/
│   └── db_descriptors.json  # 数据库描述配置
├── data/
│   ├── sandbox.sqlite       # 内置只读 SQLite 路由目标
│   ├── eval/                # 评估数据
│   └── sft/                 # SFT 训练数据
├── business_knowledge/      # 业务知识文件
│   ├── metrics/             # 指标口径定义
│   ├── faq/                 # 常见问题
│   └── mappings/            # 实体值映射 JSON
├── models/                  # 模型存放目录
└── tests/                   # 单元测试 + E2E
```

## 工作流详解

### 1. Router（数据库路由）
根据用户查询语义，将请求路由到目标数据库并加载对应 SQL 方言规则。

### 2. Planner（查询规划）
- 检索相关表结构（BM25 + embedding 混合检索）
- 检索业务知识库中的指标定义、常见口径
- 链接实体值映射（如 "北京" → `city_id=110000`）
- 生成结构化的执行计划（主表、关联、过滤、聚合、排序）

### 3. Coder（SQL 生成）
- 根据 Planner 的执行计划和完整表结构生成 N 个 SQL 候选
- 默认 N=3，失败时自动降温和重试

### 4. Executor（执行与选择）
- 候选 SQL 在沙箱数据库逐条执行
- 一致性选择器（可选 Judge LLM）评估结果语义一致性
- 选出最优 SQL，失败则回退修复并重试（默认最多 3 轮）

## 离线训练

训练链路按设计文档拆为 `Data Distillation -> SFT -> DPO -> GRPO -> Model Registry`。本仓库只保留训练前的配置与数据质检工具；当前验收范围不包含训练执行，真正的模型训练留给后续 GPU 环境。

```bash
# 生成 SFT、SFT 合并、DPO、DPO 合并、GRPO、DeepSpeed 和 dataset_info 配置
python -m text_to_sql.training init --output training_artifacts

# 校验 LlamaFactory Alpaca SFT 数据
python -m text_to_sql.training validate sft data/text2sql_sft_cot.jsonl

# 校验 DPO 偏好对
python -m text_to_sql.training validate dpo data/text2sql_dpo_aligned.jsonl

# 校验 GRPO Prompt/Reward 数据，确保 prompt 不暴露 gold_sql
python -m text_to_sql.training validate grpo data/text2sql_rl_train.jsonl

# 按语义/SQL AST/Schema 复合指纹去重，并按业务模板防泄漏切分
python -m text_to_sql.training split data/text2sql_rl.jsonl \
  --output data --prefix text2sql_rl

# 配置 target_db 到训练沙箱的库级路由；export 会逐条执行 Gold SQL
export TEXT2SQL_TRAINING_DB_URLS='{"docker_postgres":"postgresql+psycopg2://...","local_sqlite":"sqlite:///..."}'
export TEXT2SQL_REDIS_URL='redis://127.0.0.1:6379/0'

# 最终质量门禁。sensitive-fields.json 必须由数据负责人维护，不能用空清单绕过
# TEXT2SQL_EVAL_SHA256 必须来自受控评测集清单，不能在门禁执行时临时重算
export TEXT2SQL_EVAL_SHA256='<fixed-evaluation-jsonl-sha256>'
python -m text_to_sql.training quality-gate sft data/text2sql_sft_cot.jsonl \
  --eval-path data/eval/text2sql_eval.jsonl \
  --sensitive-fields data/sensitive-fields.json
python -m text_to_sql.training quality-gate dpo data/text2sql_dpo_aligned.jsonl \
  --sensitive-fields data/sensitive-fields.json
python -m text_to_sql.training quality-gate grpo data/text2sql_rl.jsonl \
  --sensitive-fields data/sensitive-fields.json

# 切分后的最终验收必须严格为 8K/1K/1K，并保持业务模板隔离
python -m text_to_sql.training quality-gate-grpo-split \
  --train data/text2sql_rl_train.jsonl \
  --valid data/text2sql_rl_valid.jsonl \
  --holdout data/text2sql_rl_holdout.jsonl

# 通过 Gold SQL 预检后转换为 veRL 直接读取的 Parquet
python -m text_to_sql.training export-grpo data/text2sql_rl_train.jsonl \
  --output data/text2sql_rl_train.parquet
python -m text_to_sql.training export-grpo data/text2sql_rl_valid.jsonl \
  --output data/text2sql_rl_valid.parquet
```

默认切分要求每条记录提前提供 `query_semantic_fingerprint`、`sql_ast_fingerprint`、`schema_fingerprint` 和 `business_template_id`。前三项组成样本去重键，重复样本只保留第一条；切分只以 `business_template_id` 分组，确保同一业务模板不会跨 train/valid/holdout。切分器先在一个最大模板组的容差内生成候选切分，随后必须通过 `quality-gate-grpo-split` 的严格 8K/1K/1K 验收；不能满足时应调整数据或模板分组，不能跳过门禁。只有明确指定 `--group-key` 时才使用不去重的单字段旧式分组。

最终质量门禁不是格式检查的别名。SFT/DPO 记录需额外携带 `target_db`、`dialect`、`gold_result_signature`、`reward_meta.preserve_result_order`、`reward_meta.result_limit` 和 `reward_meta.max_estimated_rows`，门禁会在库级路由选中的真实沙箱中执行标签 SQL。DPO 的 chosen/rejected 必须得到同一结果签名，并提供 `preference_verified=true` 与非空 `preference_reason`；若双方都有执行计划成本，chosen 不能更昂贵。所有最终入库记录必须带 `schema_verified=true`、`business_definition_verified=true` 及去重指纹；Medium/Hard SFT 还必须提供至少两条编号推理步骤和 `reasoning_verified=true`。SFT 的 `query_embedding` 会与固定的 2,500 条评测集真实 embedding 做余弦相似度检查，评测集必须满足 Easy/Medium/Hard=750/1250/500、ID 唯一且文件 SHA-256 与受控清单一致，训练样本相似度超过 0.92 直接拒绝。额外元数据不会被 LlamaFactory 的列映射送入模型。

SFT/DPO 配置各保留 10% 数据用于训练中验证，因此质量门禁要求源数据至少为 77,778 条 SFT 样本和 22,223 对 DPO 样本，确保实际参与参数更新的数据仍不少于文档规定的 70K/20K。SFT 还会校验 Easy 样本约 70% 不含 `<think>`，并要求 Medium/Hard 样本包含经过审核的结构化 `<think>`。所有阶段的 `preserve_result_order` 必须与标签 SQL 是否含顶层 `ORDER BY` 一致；GRPO Prompt 的 Gold SQL 泄漏检测会忽略空白、注释、标识符引号、字段限定、表别名以及可交换谓词顺序差异。最终 GRPO 分片门禁会再次要求 Query/SQL AST/Schema 三类指纹完整，并在 train/valid/holdout 并集上拒绝重复指纹。

模型产物顺序固定为 `SFT LoRA Adapter -> SFT 合并模型 -> 新 DPO LoRA Adapter -> DPO 合并模型 -> veRL GRPO`。DPO 以 SFT 合并模型新建 Adapter；在 LlamaFactory 0.9.5 的 LoRA DPO 中，reference 通过临时禁用同一模型的 Adapter 计算，不加载第二份 reference 模型。DeepSpeed 的 CPU Offload 只用于 optimizer state。GRPO 只读取 DPO 合并模型。

GRPO 样本必须携带 `target_db`，由该字段选择训练沙箱 URL，并由 URL 的 SQLAlchemy backend 决定实际方言；样本中的 `dialect` 仅作一致性声明，与路由库类型不一致时直接拒绝。每条样本还必须预计算非空 `gold_result_signature`，并显式给出 `reward_meta.non_empty_result=true`、`reward_meta.preserve_result_order` 和正整数 `reward_meta.result_limit`。`export-grpo` 会按库级路由对每条 Gold SQL 做方言 AST 校验、沙盒校验和一次真实执行；执行时读取 `result_limit + 1` 行，发现结果触顶即拒绝，因此训练中的候选不能通过主动截断骗取相同 signature。训练时只执行候选 SQL，不会为每条 rollout 重复执行 Gold SQL。

GRPO reward 公式与文档保持一致：`R_total = R_format * (R_exec + 0.2 * R_judge - R_penalty)`，其中格式校验、SQL 安全检查、带方言超时的 EXPLAIN/沙盒执行和结果集 signature 对比均在 `text_to_sql.training.rewards` 中提供。异步 Reward 同时返回优化用 `score`、组过滤用二值 `execution_correct` 以及格式、执行、Judge、惩罚分项；V1 `BoundedReplayBuffer` 会过滤组内全对或全错的无优势信号、限制补充生成预算，并在上游清除轨迹前把完整 prompt、候选输出和 Reward 指标分别写入 SFT/Bad Case 回流池。GRPO 配置固定 `total_training_steps=2500`，并把 `total_epochs` 保持在足以达到该步数的 30。当前实现按本地资源约束使用回环地址上的 `qwen3.5:4b` Judge，禁止将训练样本发送到远程 Judge；veRL 启动前需设置 `TEXT2SQL_REWARD_PATH`、`TEXT2SQL_REPLAY_BUFFER_PATH`、`TEXT2SQL_SFT_BACKFLOW_PATH`、`TEXT2SQL_BAD_CASE_BACKFLOW_PATH`、`TEXT2SQL_TRAINING_DB_URLS`、`TEXT2SQL_REDIS_URL`，可用 `TEXT2SQL_JUDGE_BASE_URL` 覆盖本地 Ollama 地址。`TEXT2SQL_TRAINING_DB_URLS` 必须是 JSON 对象，例如 `{"docker_postgres":"postgresql+psycopg2://...","local_sqlite":"sqlite:///..."}`。Oracle 路由要求沙箱账户能够写入 `PLAN_TABLE`；执行计划读取采用 `EXPLAIN PLAN SET STATEMENT_ID` 后查询根节点并回滚。训练环境还必须把仓库根目录加入 `PYTHONPATH`，因为 veRL 会按文件路径动态加载 Reward 和 ReplayBuffer；`init` 会输出两个模块的绝对路径、两个回流池路径以及使用绝对 Hydra 配置路径的 GRPO 命令。

GPU 环境按 `text_to_sql/training/TRAINING_ENVIRONMENTS.md` 分开创建：SFT/DPO 使用 `requirements-sft-dpo.txt`；GRPO 从 veRL 提交 `fc6ca747eb20aaf5ff8fc5e805468790292c79f7` 自带的 `uv.lock` 执行 `uv sync --extra vllm --extra fsdp --frozen`，再用 `--no-deps` 安装精确版本的 `requirements-grpo.txt` overlay 并执行 `uv pip check`。禁止合并两套环境。`init` 会复制三份环境契约到产物根目录；这些清单不用于本地 Windows 安装，本地只运行数据校验和离线单元测试。

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `llm.planner.model` | Planner LLM 模型 | `qwen3.5:4b` |
| `llm.coder.model` | Coder LLM 模型 | `qwen3.5:4b` |
| `embedding.model` | Schema/业务知识/缓存/路由 embedding | `bge-m3:latest` |
| `llm.judge` | Judge LLM 配置（null 时禁用一致性选择） | `null` |
| `database.targets` | `target_db` 到只读数据库连接的映射 | `docker_postgres` + `local_sqlite` |
| `agent.max_candidates` | 候选 SQL 数量 | `3` |
| `agent.max_retries` | 最大重试轮数 | `3` |
| `agent.result_limit` | 返回行数上限 | `100` |
| `retrieval.table_top_k` | 检索返回表数 | `10` |
| `retrieval.column_top_k` | 检索返回到数 | `20` |
| `retrieval.business_kb_top_k` | 业务知识检索条数 | `3` |
| `retrieval.similarity_threshold` | 缓存相似度阈值 | `0.95` |

## 依赖

```
fastapi / uvicorn          # Web API
langgraph                  # 多 Agent 工作流
redis                      # 语义缓存和检索索引
elasticsearch              # Value-Level 实体索引
apscheduler                # 元数据定时刷新
structlog                  # JSON 结构化日志
prometheus-client          # 监控指标
sqlalchemy / sqlglot       # 数据库连接、方言 AST 与结果限制
psycopg2 / pymysql         # PostgreSQL / MySQL 驱动
numpy / jieba / rank-bm25  # 混合检索
```

## 运行测试

```bash
cd text_to_sql
python -m pytest tests/ -v
```

## 压力测试

先启动 API，再执行有界并发测试。`--warmup` 会先运行一次完整 Agent 链路，随后并发请求命中语义缓存，适合资源有限的本机：

```bash
python -m text_to_sql.runtime.stress_test \
  --base-url http://127.0.0.1:8011 \
  --requests 12 \
  --concurrency 2 \
  --warmup \
  --query "查询前5个用户"
```

工具会输出成功数、失败数、缓存命中数、吞吐量以及平均/P50/P95/最大延迟。若要压测非缓存 Agent 路径，使用不同问题且不要添加 `--warmup`；本机 `qwen3.5:4b` 建议并发不超过 2。
