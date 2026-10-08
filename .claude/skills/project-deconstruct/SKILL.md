---
name: project-deconstruct
description: |
  解读和学习一个多 Agent 项目的完整架构与实现。用于系统地理解项目的技术选型、模块设计、
  实现细节和演进思路。当用户说「解读这个项目」「帮我理解这个项目」「拆解这个项目」
  「这个项目怎么做的」「项目架构是什么」「学一下这个项目」「deconstruct」等时触发。
  也适用于用户说要「按照模块学习」「搞清楚每个模块怎么实现的」「最小知识优先」等场景。
---

# Project Deconstruct — 项目解读与学习

## 概述

你是一个项目解读专家。当用户想系统学习一个项目时，你的任务是**按照最小知识优先的原则**，
先建立全局认知，再逐步深入到每个模块的实现细节。

**核心教学原则：**
1. **先画图再讲字** — 每个阶段先用 Mermaid 图建立视觉认知
2. **先讲 Why 再讲 How** — 每个模块先说"解决了什么问题"，再说"怎么实现的"
3. **导航式深潜** — 点到即止，具体代码细节指引用户去看源文件
4. **演进驱动理解** — 从 V1 痛点到 V3 突破，理解每个设计决策的来龙去脉
5. **落笔成文** — 每个阶段讲解完成后，**必须自动生成对应的 Markdown 笔记**，写入项目目录下

---

## 当前项目上下文

这个 Skill 默认解读的项目是 **居丽叶的简历项目6：差旅出行助手（Aligo）**。

项目根目录：`project/居丽叶简历项目6：差旅出行助手/`

如果你在解读其他项目，先在对话中确认项目的目录结构和关键文件。

### 关键路径速查

| 类型 | 路径 |
|------|------|
| 项目入口 + 主流程 | `cli.py` |
| 意图识别 Agent | `agents/intention_agent.py` |
| 调度编排 Agent | `agents/orchestration_agent.py` |
| 懒加载注册器 | `agents/lazy_agent_registry.py` |
| 记忆管理器 | `context/memory_manager.py` |
| 短期记忆 | `context/short_term_memory.py` |
| 长期记忆 | `context/long_term_memory.py` |
| 6 个 Skill 插件 | `.claude/skills/{ask-question,event-collection,memory-query,plan-trip,preference,query-info}/` |
| Skill 加载器 | `utils/skill_loader.py` |
| 熔断器 | `utils/circuit_breaker.py` |
| 容错重试 | `utils/llm_resilience.py` |
| 配置文件 | `config.py`, `config_agentscope.py` |
| 面试题（28篇） | `面试题/` |

---

## 📝 笔记输出规则（核心约束）

**解读必须落笔成文。** 不能只在对话里讲一遍就结束，每完成一个阶段/模块的讲解，
**必须自动生成对应的 Markdown 笔记**，写入项目目录。

### 输出目录

所有生成的笔记写入：

```
project/居丽叶简历项目6：差旅出行助手/解读笔记/
```

### 文件命名与对应关系

| 讲解内容 | 生成的笔记文件 |
|----------|---------------|
| 阶段一：架构鸟瞰 | `00-架构总览.md` |
| 阶段二：三轮演进 | `01-三轮优化演进.md` |
| 阶段三 · 模块1：意图识别 | `02-意图识别模块.md` |
| 阶段三 · 模块2：双层记忆 | `03-双层记忆系统.md` |
| 阶段三 · 模块3：RAG 知识库 | `04-RAG知识库.md` |
| 阶段三 · 模块4：并行调度 | `05-并行调度.md` |
| 阶段三 · 模块5：Skill插件化 | `06-Skill插件化与懒加载.md` |
| 阶段三 · 模块6：稳定性保障 | `07-稳定性保障.md` |
| 阶段四：八股理论 | `08-八股知识.md` |
| 阶段五：开发与团队 | `09-开发思路与团队.md` |
| 全部讲完时 | `_index.md`（总目录导航） |

### 笔记格式要求

每篇笔记必须是**完整、可独立阅读**的 Markdown 文件，包含：

1. **YAML frontmatter**：`tags`、`related`（链接到面试题和源码）
2. **Mermaid 图**：保留讲解时画的架构图/流程图
3. **结构化内容**：小节标题 + 表格 + 要点列表
4. **面试题链接**：用 Wiki-link 链接到对应的面试题文件
5. **源码导航**：指向关键文件的路径和行号

### 生成时机

- **阶段一 + 阶段二**：讲完后一起生成 `00-架构总览.md` + `01-三轮优化演进.md`
- **阶段三每个模块**：每讲完一个模块，立即生成对应的笔记文件
- **阶段四**：全部八股讲完后生成 `08-八股知识.md`
- **阶段五**：讲完后生成 `09-开发思路与团队.md`
- **全部完成**：生成 `_index.md` 总目录

### 生成流程

```
讲解完成 → 用 Write 工具写 Markdown 文件 → 告诉用户「已生成 → 解读笔记/XX.md」
```

**重要**：不要在对话中让用户手动复制粘贴。你必须**直接调用 Write 工具写文件**。

---

## 阶段一：架构鸟瞰（最小知识优先）

### 1.1 先给一句话定义

> 基于 **AgentScope** 框架的多 Agent 差旅出行助手，采用 **Plan-and-Execute** 架构，
> 经过三轮优化（记忆/RAG/并行），将意图准确率从 **65% 提升到 90%+**，
> 响应时间从 **30s 降到 15s**，QPS 从 **100 提升到 500+**。

### 1.2 画出整体架构图

用 Mermaid 绘制数据流，让用户一眼看到请求的全路径：

```mermaid
flowchart TB
    U[👤 用户输入] --> CLI[CLI 交互层<br/>cli.py]
    CLI --> |自然语言| IA[IntentionAgent<br/>意图识别 · 四步推理]

    IA --> |JSON 调度计划| OA[OrchestrationAgent<br/>协调调度器]

    subgraph P1[Priority 1 · 并行执行 asyncio.gather]
        EC[EventCollection<br/>事项收集]
        PR[Preference<br/>偏好管理]
        MQ[MemoryQuery<br/>记忆查询]
        RAG[RAGKnowledge<br/>知识库查询]
        IQ[InformationQuery<br/>信息查询 · 联网]
    end

    OA --> |同优先级并行分发| P1

    subgraph P2[Priority 2 · 串行收口]
        IP[ItineraryPlanning<br/>行程规划]
    end

    P1 --> |所有结果聚合| P2
    P2 --> |最终方案| OA

    subgraph INFRA[基础设施层]
        MEM[双层记忆<br/>Redis短期 + JSON长期]
        KB[RAG知识库<br/>Milvus + BGE-m3]
        CB[稳定性保障<br/>熔断器 + 重试 + 健康检查]
    end

    OA -.-> |读写| INFRA
    OA --> |结果| CLI
    CLI --> U

    style IA fill:#e3f2fd,stroke:#1565c0
    style OA fill:#f3e5f5,stroke:#7b1fa2
    style P1 fill:#e8f5e9,stroke:#2e7d32
    style P2 fill:#fff3e0,stroke:#e65100
    style INFRA fill:#fafafa,stroke:#616161
```

### 1.3 核心数字速查

| # | 指标 | 数字 | 怎么来的 |
|---|------|------|----------|
| 1 | 意图准确率 | **65% → 90%+** | 关键词匹配→LLM语义理解 |
| 2 | 知识问答准确率 | **95%** | Milvus + BGE-m3 + 混合检索 |
| 3 | 偏好记忆准确率 | **95%** | LLM 语义判断追加 vs 覆盖 |
| 4 | 响应时间 | **30s → 15s** | 串行→优先级并行调度 |
| 5 | Token 消耗 | **4500-6000** | 一次完整行程规划 |
| 6 | QPS | **100 → 500+** | Redis缓存 + 异步架构 |
| 7 | 启动速度 | **3 秒以内** | LazyAgentRegistry 懒加载 |
| 8 | 测试集 | **1000 条** | 真实脱敏用户语料 |

### 1.4 技术栈一张图

```
框架层：  AgentScope 1.0.16 (阿里开源, Actor模型+Msg通信)
架构：    Plan-and-Execute (先规划再执行)
模型：    豆包大模型 (doubao-seed-1-6-flash)
存储：    PostgreSQL(长期) + Redis(短期缓存) + Milvus(向量)
嵌入：    BGE-small-zh-v1.5 (本地部署)
搜索：    DuckDuckGo + wttr.in 天气
界面：    Rich CLI (终端)
```

---

## 阶段二：三轮优化演进（理解「为什么」）

这个项目不是一步到位的。三轮优化，每轮解决一个核心痛点。

先给一张总览图：

```mermaid
flowchart LR
    V1[V1 基础版<br/>❌ 关键词匹配<br/>❌ 串行调度<br/>❌ 没有记忆]
    -->|准确率仅65%<br/>响应30s| V2

    V2[V2 记忆+RAG<br/>✅ 双层记忆<br/>✅ RAG知识库<br/>✅ 联网搜索]
    -->|缺并行、意图弱| V3

    V3[V3 高性能<br/>✅ LLM语义意图<br/>✅ 优先级并行<br/>✅ Skill插件化]
    -->|90%+/15s/500+QPS| V4

    V4[V4 生产就绪<br/>✅ 熔断器<br/>✅ 重试退避<br/>✅ 健康检查]
```

### V1 → V2 「记」— 让系统有记忆

| 维度 | 说明 |
|------|------|
| **痛点** | 系统完全不记得用户偏好，每次重复说；政策类全靠 LLM 编造（幻觉严重） |
| **方案** | 双层记忆系统 + RAG 知识库 |
| **短期记忆** | Redis 滑动窗口，保留最近 10 轮对话，TTL 1 小时 |
| **长期记忆** | JSON 文件（架构设计为 PG JSONB），持久化偏好/行程/聊天历史 |
| **偏好管理** | PreferenceAgent 基于 LLM 语义区分「追加」("我还喜欢如家") vs 「覆盖」("我搬家了") |
| **异步总结** | LLM 压缩历史对话为 200 字摘要，缓存 Redis（TTL 30min） |
| **RAG 知识库** | Milvus + BGE-m3，存差旅政策/城市攻略/FAQ，混合检索 top3 |
| **防幻觉** | 四层漏斗：Prompt 约束 → 检索注入 → 阈值拦截 → 原文溯源 |
| **指标** | 偏好记忆准确率 **95%**，知识问答准确率 **95%** |

### V2 → V3 「快」— 让系统快起来

| 维度 | 说明 |
|------|------|
| **痛点** | 关键词匹配意图准确率仅 65%（同义词/复合意图全挂）；串行调度慢（30s） |
| **方案** | LLM 语义意图识别 + 优先级并行调度 |
| **意图升级** | 关键词→LLM 语义理解，支持 **6 大类意图**、多意图识别、置信度输出 |
| **上下文消歧** | 引入短期记忆，"北京酒店多少钱"→如果刚才聊行程=信息查询，问历史=记忆查询 |
| **并行调度** | Priority 1 五个 Agent（asyncio.gather 并行收集信息）→ Priority 2 行程规划串行收口 |
| **缓存层** | Redis 缓存偏好热数据（命中率 85%），减少 PG 查询 |
| **插件化** | Skill Plugins + LazyAgentRegistry 懒加载（启动 3 秒内） |
| **指标** | 准确率 **90%+**，响应 **15s**（-50%），QPS **100→500+** |

### 三轮口诀

```
第一轮「记」：Redis + PG + 异步LLM总结 → 95%
第二轮「查」：Milvus + BGE-m3 + Google Search → 95%
第三轮「快」：语义意图 + 并行调度 → 90%+、15s
```

---

## 阶段三：模块深潜（逐一拆解）

以下 6 个模块，每个按「解决什么问题 → 怎么实现 → 技术权衡 → 面试题链接」展开。

当用户说「讲一下 XX 模块」「XX 怎么实现的」时，对应展开该模块。

### 模块 1：意图识别（IntentionAgent）

**源码**：`agents/intention_agent.py`（302行，核心在 `reply()` 方法 L36-L301）

**解决了什么问题？**
V1 用关键词匹配（看到"去"→行程规划，看到"喜欢"→偏好），准确率只有 65%。
同义词（"溜达""逛逛"）、复合意图（"我想去北京喜欢住汉庭"=两个意图）、
上下文依赖（"北京酒店多少钱"在不同语境下意图不同）全部无法处理。

**怎么实现的？**

```mermaid
flowchart LR
    Q[用户 Query] --> S1[Step1: 推理 reasoning]
    S1 --> S2[Step2: 多意图识别 intents+confidence]
    S2 --> S3[Step3: Query改写]
    S3 --> S4[Step4: 调度计划 agent_schedule+priority]
    S4 --> J[JSON输出]
```

IntentionAgent 的四步推理（Prompt 在 L106-L213）：
1. **推理**：分析 query 核心诉求，结合对话历史消歧
2. **多意图识别**：识别所有意图 + 置信度（0-1），支持复合意图
3. **Query 改写**：口语转标准化，补全省略信息
4. **调度计划**：决定调哪些 Agent、优先级、调用顺序

**关键设计决策：**
- 支持 **6 大类意图**：itinerary_planning / memory_query / preference / rag_knowledge / information_query / event_collection
- 输出**严格 JSON 格式**，带容错解析（L258-L273：提取 JSON + 降级默认值）
- **上下文消歧**：从短期记忆中读取最近对话，区分同一关键词的不同意图
- **模糊时间处理**：Prompt 注入当前时间（年月日+星期），LLM 自动推断「明天」「下周二」
- **单一 LLM 调用**（vs ReAct 的多次调用），节省 Token

**技术权衡：**
- 为什么不继续优化关键词？→ 维护成本指数增长，永远覆盖不完
- 为什么不用 ReAct？→ 每次循环调 LLM 太慢太贵，P&E 一次规划执行效率更高
- 为什么输出 JSON？→ 下游调度器需要结构化数据决定并行策略

📖 **相关面试题**：[[project/居丽叶简历项目6：差旅出行助手/面试题/05-意图识别升级|05-意图识别升级]]、[[project/居丽叶简历项目6：差旅出行助手/面试题/Q4-模糊时间处理|Q4-模糊时间]]

---

### 模块 2：双层记忆系统

**源码**：
- `context/memory_manager.py`（253行）
- `context/short_term_memory.py`（107行）
- `context/long_term_memory.py`（359行）

**解决了什么问题？**
V1 完全没记忆——用户每次都要重新说「我喜欢汉庭」「我家在天津」。
旅行助手需要记住三类信息：当前会话聊到哪了（短期）、用户偏好和历史行程（长期）。

**怎么实现的？**

```mermaid
flowchart TB
    subgraph SHORT[短期记忆 · 会话级]
        REDIS[滑动窗口队列<br/>最近10轮对话<br/>TTL 1小时]
    end

    subgraph LONG[长期记忆 · 跨会话持久化]
        PG[(JSON文件存储<br/>架构设计为PG JSONB)]
        PREF[用户偏好<br/>酒店/航空/座位/预算]
        TRIP[历史行程<br/>出发地/目的地/时间/目的]
        CHAT[聊天历史<br/>完整对话记录]
    end

    subgraph CACHE[缓存层]
        RC1[偏好热数据<br/>命中率85%]
        RC2[LLM总结结果<br/>TTL 30分钟]
    end

    SHORT --> |会话结束清空| LONG
    CACHE --> |Write-Through写| LONG
    CACHE --> |Lazy Loading读| PG

    ASYNC[异步LLM总结<br/>压缩为200字摘要] --> RC2
```

**短期记忆** (`short_term_memory.py`)：
- 双端队列（deque），`max_turns=10`（即 20 条消息，L27-L28）
- 自动淘汰旧消息（超 10 轮舍弃最早，L49-L52）
- 提供 `get_recent_context(n_turns)` 和 `get_context_string()` 两种查询

**长期记忆** (`long_term_memory.py`)：
- JSON 文件存储，字典格式偏好（V2 已迁移为列表格式，`_migrate_data()` L60-L112）
- 三类数据：preferences（偏好列表）、chat_history（聊天记录）、trip_history（行程记录）
- 统计信息：常去目的地、总行程数（L321-L333）
- 数据迁移兼容：自动修复旧格式 + 嵌套 bug（L92-L102）

**异步 LLM 总结** (`memory_manager.py` L129-L252)：
- 每次对话前异步调用 LLM，总结历史聊天+行程为 **200 字以内摘要**
- 注入 IntentionAgent 的 system 消息，省 Token 又不丢信息
- 结果可缓存在 Redis（架构设计，当前版本未完整实现）

**技术权衡：**
- 为什么保留 10 轮？→ 试过 5 轮（不够连贯）和 15 轮（Token 压力大），10 轮是最优平衡
- 为什么用 JSON 而非 PG？→ 当前是 Demo 版本，README 明确写了 PG 是生产方案
- 为什么选 PG over MySQL？→ JSONB 高效索引半结构化数据 + MVCC 读写不阻塞（适合 QPS 500+）

📖 **相关面试题**：[[project/居丽叶简历项目6：差旅出行助手/面试题/03-双层记忆系统|03-双层记忆系统]]、[[project/居丽叶简历项目6：差旅出行助手/面试题/Q2-偏好判断|Q2-偏好判断]]

---

### 模块 3：RAG 知识库

**源码**：`.claude/skills/ask-question/script/agent.py`、`init_knowledge_base.py`
**配置**：`config.py` (RAG_CONFIG)

**解决了什么问题？**
差旅政策（报销标准/预订规则）、城市攻略、FAQ 等知识不能让 LLM 凭记忆"编"。
需要基于真实文档检索+生成，还要防止 LLM 幻觉。

**怎么实现的？**

```mermaid
flowchart TB
    DOC[8类文档<br/>政策/报销/预订<br/>FAQ/紧急/指南] --> CHUNK[滑动窗口切分<br/>512 token/块<br/>重叠50 token]

    CHUNK --> EMBED[BGE-small-zh-v1.5<br/>本地Embedding]
    EMBED --> MILVUS[(Milvus Lite<br/>向量数据库)]

    Q[用户问题] --> QE[BGE Embedding]
    QE --> HYBRID{混合检索}

    HYBRID --> |向量语义| VEC[余弦相似度<br/>top10]
    HYBRID --> |关键词| BM25[BM25<br/>top10]

    VEC --> RRF[RRF融合排序]
    BM25 --> RRF

    RRF --> TOP3[取 top3<br/>相似度阈值过滤]
    TOP3 --> LLM[LLM生成答案<br/>附原文溯源]

    LLM --> GUARD[四层防幻觉漏斗]

    subgraph GUARD[ ]
        G1[① Prompt硬约束<br/>不准编，找不到直说]
        G2[② 检索注入<br/>知识片段打标签圈边界]
        G3[③ 阈值拦截<br/>低于阈值直接拒答]
        G4[④ 原文溯源<br/>附原始文档供核对]
    end
```

**关键设计决策：**
- **混合检索**（向量语义 + BM25 关键词）→ 语义理解和精确匹配互补
- **RRF 融合** → 两路各取 top10，融合后取 top3，减少无关信息注入
- **滑动窗口切分**（512 token/块，重叠 50 token）→ 防止关键信息卡在边界
- **本地部署 BGE**（`data/models/bge-small-zh-v1.5/`）→ 无需联网，响应更快
- **四层防幻觉**（从粗到细）→ 最终准确率 95%

**技术权衡：**
- 为什么用 Milvus 而非 Faiss？→ Milvus 支持分布式+混合检索+多种索引算法（HNSW/IVF/FLAT），Faiss 偏单机
- 为什么用 BGE-m3 而非 text2vec？→ BGE-m3 多语言+8192 token 长文本+三表征输出，中文效果更好
- 为什么混合检索？→ 纯向量检索对精确关键词（如"报销比例 80%"）可能漏掉，BM25 补充

📖 **相关面试题**：[[project/居丽叶简历项目6：差旅出行助手/面试题/04-RAG知识库|04-RAG知识库]]、[[project/居丽叶简历项目6：差旅出行助手/面试题/10-防幻觉Token容错|10-防幻觉]]

---

### 模块 4：并行调度

**源码**：`agents/orchestration_agent.py`（486行，核心在 `reply()` L60-L149、`_execute_parallel_agents()` L180-L265）

**解决了什么问题？**
V1 串行调度——每个 Agent 依次执行，总时间 = 所有 Agent 耗时之和 = 30 秒。
用户等太久，体验差。

**怎么实现的？**

```mermaid
flowchart TB
    IA[IntentionAgent<br/>输出调度计划] --> SORT[按优先级排序]

    SORT --> P1[Priority 1 · 并行]
    SORT --> P2[Priority 2 · 串行]

    subgraph P1[ ]
        direction LR
        A1[EventCollection]
        A2[Preference]
        A3[MemoryQuery]
        A4[RAGKnowledge]
        A5[InformationQuery]
    end

    P1 --> |asyncio.gather<br/>所有结果| WAIT[等待全部完成]

    subgraph P2[ ]
        A6[ItineraryPlanning<br/>整合所有结果]
    end

    WAIT --> P2
    P2 --> OUT[最终行程方案]
```

**调度逻辑**（`orchestration_agent.py`）：
1. 解析 IntentionAgent 的 `agent_schedule`（L95-L96）
2. 按 priority 分组（L107-L131）
3. 同 priority 的 Agent 用 `asyncio.gather` 并行执行（L240-L243）
4. Priority 2（行程规划）等待 Priority 1 全部完成后才启动
5. 结果聚合：`_aggregate_results()` 收集所有结果，标注 partial_failure（L350-L390）

**类比**：像做饭——先同时洗菜切菜烧水（P1 并行），备好料再下锅炒（P2 串行收口）

**关键设计决策：**
- **P1 五个 Agent 互不依赖**：信息收集类，可以同时跑
- **P2 依赖于 P1**：行程规划需要前面的所有数据
- **部分成功机制**：一个 Agent 挂了不影响其他（`return_exceptions=True`，L241），优雅降级

📖 **相关面试题**：[[project/居丽叶简历项目6：差旅出行助手/面试题/06-并行调度|06-并行调度]]、[[project/居丽叶简历项目6：差旅出行助手/面试题/Q3-Agent间通信|Q3-Agent间通信]]

---

### 模块 5：Skill 插件化 + 懒加载

**源码**：
- `agents/lazy_agent_registry.py`（181行）
- `utils/skill_loader.py`（134行）
- `.claude/skills/` 下 6 个 Skill 目录

**解决了什么问题？**
Agent 多了以后，硬编码导入 + 全部预加载 → 启动慢、耦合高、加新 Agent 要改核心代码。

**怎么实现的？**

```mermaid
flowchart TB
    subgraph DISCOVER[启动时 · 扫描阶段]
        SCAN[扫描 .claude/skills/] --> MATCH[匹配 script/agent.py]
        MATCH --> REG[注册到 _skill_map<br/>只登记，不加载]
    end

    subgraph LOAD[首次调用时 · 懒加载]
        CALL[Orchestrator 请求 Agent] --> CACHE{缓存中有?}
        CACHE -->|有| RETURN[直接返回]
        CACHE -->|无| IMPORT[importlib 动态导入]
        IMPORT --> FIND[inspect 查找 AgentBase 子类]
        FIND --> |检查签名| INJECT[注入 model + memory_manager]
        INJECT --> STORE[存入 _cache]
        STORE --> RETURN
    end

    DISCOVER --> LOAD
```

**LazyAgentRegistry 两步机制**（`lazy_agent_registry.py`）：
1. **`_discover_skills()`**（L56-L74）：启动时扫描 `.claude/skills/`，找 `script/agent.py`，只登记路径不加载
2. **`__getitem__()`**（L90-L154）：首次调用时动态导入模块 → 查找 AgentBase 子类 → 检查构造函数签名注入依赖 → 实例化 → 缓存复用

**SkillLoader**（`skill_loader.py`）：
- 解析 SKILL.md 的 YAML frontmatter，提取 name 和 description
- `get_skill_prompt()` 生成意图识别 Prompt 中的 Skills 列表
- `get_skill_content()` 获取完整 Markdown 内容用于执行阶段注入

**三大好处：**
- **零配置**：加新 Agent 扔进目录就行
- **热插拔**：增删 Skill 不影响核心代码
- **快速启动**：懒加载让启动压到 **3 秒以内**

**技术权衡：**
- Python 动态导入的坑：路径管理（L114-L116 确保 `sys.path` 包含项目根目录）、依赖注入（L138-L140 用 `inspect.signature` 检查是否需要 memory_manager）
- 参考了 Claude Code 的 Skill 设计模式

📖 **相关面试题**：[[project/居丽叶简历项目6：差旅出行助手/面试题/07-Skill插件化与缓存|07-Skill插件化]]、[[project/居丽叶简历项目6：差旅出行助手/面试题/Q1-六个Skills|Q1-六个Skills]]

---

### 模块 6：稳定性保障

**源码**：
- `utils/circuit_breaker.py`（123行）
- `utils/llm_resilience.py`
- `config.py` (RESILIENCE_CONFIG)

**解决了什么问题？**
LLM API 不稳定——超时、限流、宕机。不能让整个系统跟着崩溃。

**怎么实现的？**

```
熔断器（Circuit Breaker）
├── CLOSED：正常调用，记录失败次数
├── OPEN：连续失败 5 次→熔断，直接返回「服务不可用」
│   └── 60 秒后自动进入 HALF_OPEN
└── HALF_OPEN：放行试探请求
    ├── 连续成功 2 次→恢复到 CLOSED
    └── 失败→回到 OPEN

指数退避重试
├── 重试 3 次
├── 间隔：1s → 2s → 4s
└── 仅对超时/429/5xx 等可重试错误生效

健康检查
├── 会话内：输入 health 查看状态
└── 命令行：python cli.py health（退出码 0/1，便于监控）
```

**在 cli.py 中的集成**（L158-L166、L186-L228）：
- 每次 LLM 调用前检查 `circuit_breaker.raise_if_open()`
- 用 `retry_with_backoff` 包裹意图识别和编排调用
- 成功记录 `record_success()`，失败记录 `record_failure()`

**容错四级策略：**
1. **单 Agent 级**：try-catch 捕获异常记日志，不往上抛
2. **并发级**：`asyncio.gather(return_exceptions=True)`，一个挂了其他照跑
3. **重试机制**：指数退避 3 次
4. **部分成功**：多个 Agent 部分成功部分失败，交付能交付的

**核心原则**：**单点故障不扩散，部分成功也交付**

📖 **相关面试题**：[[project/居丽叶简历项目6：差旅出行助手/面试题/10-防幻觉Token容错|10-防幻觉Token容错]]

---

## 阶段四：八股知识（通用概念）

当用户想了解项目背后的通用理论时，逐一展开以下 7 个八股知识点。
每个知识点结合项目中的**具体例子**讲解，而不仅仅讲抽象概念。

### 八股清单

| 序号 | 主题 | 面试题文件 | 核心内容 |
|------|------|-----------|----------|
| 1 | Agent Skills | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股1-AgentSkills\|八股1]] | Skill 的定义、三层信息结构、渐进式暴露 |
| 2 | ReAct 模式 | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股2-ReAct\|八股2]] | Thought-Action-Observation 循环，与 P&E 对比 |
| 3 | Agent 核心模块 | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股3-Agent核心模块\|八股3]] | Profile/Memory/Planning/Action 四大模块 |
| 4 | RAG 全流程 | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股4-RAG全流程\|八股4]] | 索引→检索→增强→生成的完整 Pipeline |
| 5 | Chunking 策略 | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股5-Chunking\|八股5]] | 固定大小/滑动窗口/语义分块，优缺点对比 |
| 6 | 检索算法 | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股6-检索算法\|八股6]] | 向量检索/BM25/混合检索/RRF 融合 |
| 7 | 多 Agent 框架对比 | [[project/居丽叶简历项目6：差旅出行助手/面试题/八股7-多Agent框架对比\|八股7]] | AgentScope vs LangGraph vs AutoGen vs CrewAI |

### 讲解方式

当用户问「讲讲 ReAct」「RAG 全流程是什么」时：
1. 先读对应的八股面试题文件
2. 用项目中的**具体例子**解释（不要只讲抽象概念）
3. 画一张 Mermaid 流程图辅助理解
4. 说明「这个项目中为什么选/不选这个方案」

例如：
- 讲 ReAct 时 → 对比项目用的 P&E（Plan-and-Execute），说明为什么不用 ReAct（效率/省钱/可控）
- 讲 RAG 时 → 直接拿项目中 Milvus+BGE+混合检索+四层防幻觉的完整 Pipeline 作为案例
- 讲 Chunking 时 → 解释项目中 512 token + 50 token 重叠的设计理由

---

## 阶段五：开发思路与团队

### Vibe Coding 三阶段

[[project/居丽叶简历项目6：差旅出行助手/面试题/11-VibeCoding开发思路|11-VibeCoding]]

```
阶段一：架构我定 → 人花大量时间做架构规划，AI 做快速调研对比
阶段二：AI写代码 → 人写需求描述+接口规范，AI 生成初版，人逐行 review
阶段三：数据说话 → 1000条测试集 → 65% → 分析错误 → 迭代到 90%+
```

核心总结：**人当指挥官，AI当兵**。架构判断力、需求拆解力、代码审查力，缺一不可。

### 项目分工

[[project/居丽叶简历项目6：差旅出行助手/面试题/12-项目分工|12-项目分工]]

| 角色 | 负责 |
|------|------|
| **我**（架构负责人） | 架构设计 + 核心 Agent + 性能优化 |
| **同事A** | RAG 知识库（Milvus/BGE/混合检索） |
| **同事B** | 后端 API + 前端 |

### 未来优化方向

[[project/居丽叶简历项目6：差旅出行助手/面试题/13-未来优化方向|13-未来优化方向]]

三个维度：可观测（全链路追踪）、降本（规则引擎+Handoffs）、体验（流式输出）。

---

## 附录：完整文件索引

### 面试题完整索引（28篇）

**主流程（14篇）**：
[[project/居丽叶简历项目6：差旅出行助手/面试题/00-速查卡|00-速查卡]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/01-项目背景|01-项目背景]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/02-三轮优化总览|02-三轮优化]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/03-双层记忆系统|03-双层记忆]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/04-RAG知识库|04-RAG知识库]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/05-意图识别升级|05-意图识别]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/06-并行调度|06-并行调度]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/07-Skill插件化与缓存|07-Skill插件化]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/08-核心指标|08-核心指标]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/09-选型AgentScope与PE|09-选型]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/10-防幻觉Token容错|10-防幻觉]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/11-VibeCoding开发思路|11-VibeCoding]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/12-项目分工|12-项目分工]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/13-未来优化方向|13-未来优化]]

**补充追问（7篇）**：
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q1-六个Skills|Q1]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q2-偏好判断|Q2]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q3-Agent间通信|Q3]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q4-模糊时间处理|Q4]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q5-无关问题处理|Q5]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q6-规划合理性|Q6]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/Q7-困难挑战|Q7]]

**八股文（7篇）**：
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股1-AgentSkills|八股1]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股2-ReAct|八股2]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股3-Agent核心模块|八股3]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股4-RAG全流程|八股4]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股5-Chunking|八股5]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股6-检索算法|八股6]] ·
[[project/居丽叶简历项目6：差旅出行助手/面试题/八股7-多Agent框架对比|八股7]]

### 源码索引

| 模块 | 文件 | 行数 |
|------|------|------|
| CLI 主程序 | `cli.py` | 829 |
| 意图识别 | `agents/intention_agent.py` | 302 |
| 调度编排 | `agents/orchestration_agent.py` | 486 |
| 懒加载注册 | `agents/lazy_agent_registry.py` | 181 |
| 记忆管理器 | `context/memory_manager.py` | 253 |
| 短期记忆 | `context/short_term_memory.py` | 107 |
| 长期记忆 | `context/long_term_memory.py` | 359 |
| Skill 加载器 | `utils/skill_loader.py` | 134 |
| 熔断器 | `utils/circuit_breaker.py` | 123 |
| 容错重试 | `utils/llm_resilience.py` | - |
| 配置文件 | `config.py` + `config_agentscope.py` | 37 + - |
| RAG Agent | `.claude/skills/ask-question/script/agent.py` | - |
| 行程规划 Agent | `.claude/skills/plan-trip/script/agent.py` | - |
| 偏好管理 Agent | `.claude/skills/preference/script/agent.py` | - |
| 事项收集 Agent | `.claude/skills/event-collection/script/agent.py` | - |
| 记忆查询 Agent | `.claude/skills/memory-query/script/agent.py` | - |
| 信息查询 Agent | `.claude/skills/query-info/script/agent.py` | - |

---

## 工作流程总结

当用户说「解读/学习/拆解这个项目」时：

1. **先确认项目**：如果用户没有指定项目，默认解读本 Skill 对应的差旅出行助手项目。如果用户指定了其他项目，先探索目录结构再做架构分析。

2. **按阶段推进**：
   - 先展示**阶段一 + 阶段二**（架构鸟瞰 + 三轮演进）→ **立刻生成 `00-架构总览.md` + `01-三轮优化演进.md`**
   - 然后根据用户兴趣深入**阶段三**的具体模块（一个模块一个模块来）→ **每讲完一个模块立刻生成对应笔记**
   - 当用户问概念性问题时切换到**阶段四**（八股理论）→ **讲完生成 `08-八股知识.md`**
   - 最后补充**阶段五**的开发思路和团队分工 → **生成 `09-开发思路与团队.md`**

3. **笔记生成是硬要求**：每完成一个阶段/模块的讲解，必须调用 Write 工具写文件。
   不要等用户说「帮我记下来」——讲解完成 = 自动落笔。

4. **每个模块的讲解模板**：
   ```
   ① 一句话：这个模块做什么
   ② Mermaid 图：数据流/架构
   ③ 解决什么问题（痛点）
   ④ 怎么实现的（关键设计 + 源码导航）
   ⑤ 技术权衡（为什么选 A 不选 B）
   ⑥ 面试题链接（想深入了解？看这篇）
   ⑦ → 写入笔记文件
   ```

5. **互动节奏**：
   - 每讲完一个模块，问用户「想继续深入这个模块，还是看下一个模块？」
   - 用户说「继续」时，读对应的源码文件，展开具体实现细节
   - 用户说「下一个」时，切换到下一个模块的鸟瞰视图

6. **源码导航原则**：
   - 不要大段贴代码到对话中，而是指路：「看 `intention_agent.py` 的 L106-L213」
   - 当用户要求展开时，再读具体代码行并解释

### 笔记模板参考

#### 模块笔记模板

以下是每个模块笔记的标准模板，生成时遵循此结构：

```markdown
---
tags: [项目解读, 差旅出行助手, <模块标签>]
difficulty: beginner | intermediate | advanced
prerequisites:
  - 解读笔记/00-架构总览
  - 解读笔记/01-三轮优化演进
related:
  - 面试题/<相关面试题>
---

# <模块名称>

> **一句话**：<一句话说清楚这个模块做什么>

## 架构图

```mermaid
<数据流/架构图>
```

**图释**：<一句话解释这张图>

## 解决什么问题

<痛点描述——V1 有什么问题，为什么需要这个模块>

## 怎么实现的

<关键设计决策 + 源码导航，代码片段不超过 15 行>

## 技术权衡

<为什么选 A 不选 B，表格对比>

## 源码导航

| 文件 | 关键行 | 说明 |
|------|--------|------|
| ... | ... | ... |

## 面试题

- [[面试题链接]]

---

[[解读笔记/_index|← 返回知识地图]]
```

#### _index.md 知识地图模板

**必须**采用 note-splitter 风格的学习导向知识地图。核心要素：

```markdown
---
tags: [项目解读, <项目标签>, 索引]
---

# 🗺️ <项目名> · 项目知识地图

> **学习路径**：<一句话学习建议>
> 每个知识点都标注了难度和前置要求，可以灵活跳转。

---

## 🧭 知识导航

```mermaid
mindmap
  root((项目名))
    架构鸟瞰
      00-架构总览
      01-三轮优化演进
    模块深潜
      02-模块A
      03-模块B
      ...
    拓展补充
      08-八股知识
      09-开发思路与团队
```

> **图释**：<解释三层结构，给出学习建议>

---

## 📋 知识点列表

| # | 知识点 | 难度 | 前置知识 | 状态 |
|---|--------|------|---------|------|
| 0 | [[解读笔记/00-架构总览\|标题]] | 🌱 入门 | — | ⬜ |
| 1 | [[解读笔记/01-三轮优化演进\|标题]] | 🌱 入门 | #0 | ⬜ |
| 2 | [[解读笔记/02-某模块\|标题]] | 🌿 进阶 | #0, #1 | ⬜ |
| ... | ... | ... | ... | ⬜ |

### 难度图标说明

| 图标 | 含义 | 建议 |
|------|------|------|
| 🌱 入门 | 建立全局认知，无需前置 | 先读完再往下走 |
| 🌿 进阶 | 深入具体模块，需理解整体架构 | 按兴趣选读 |
| 🌳 深入 | 需要多个模块的知识铺垫 | 学完相关模块后再看 |

### 使用建议

1. 🌱 从入门篇开始——先知道这个项目是什么
2. 🌿 按推荐顺序逐个模块深入
3. 🌿 学到哪，在状态列打 ✅
4. 🌳 深入篇留到最后
5. 🔗 每篇末尾都有面试题链接

---

## 🔗 相关资源

<面试题索引 + 源码索引 + README 链接>

---

> **提示**：学习不是线性的——遇到难点可以暂时跳过。
>
> [[面试题/00-速查卡\|← 面试速查卡]]
```

**关键要求**：
- frontmatter 必须包含 `difficulty` 字段
- 必须用 mermaid `mindmap` 而非 `flowchart` 画知识导航
- 知识点列表必须有 **难度**、**前置知识**（用 `#编号` 引用）、**状态** 三列
- 「使用建议」必须给出具体学习路径，不能是泛泛的「建议按顺序学习」
