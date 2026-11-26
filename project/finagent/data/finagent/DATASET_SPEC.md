---
title: "DATASET_SPEC"
topic: "finagent"
type: project
date: 2026-11-12
---

# FinAgent Agent 交互轨迹数据集规范

## 数据集用途

本数据集服务于三件事：

1. **SFT 微调**：训练模型在金融场景下输出合规的工具调用序列。训练入口是 `finagent/data_pipeline/training/configs/qwen2_5_14b_finagent_sft.yaml`，基座 `Qwen/Qwen2.5-14B-Instruct`，LoRA rank 64，`cutoff_len: 2048`。
2. **离线评测基线**：`finagent/data_pipeline/evaluation/offline.py` 的 `EvaluationCase` 与 `EvaluationPrediction` 用 `required_tools`、`expected_final_status`、`risk_flag_codes` 三项做对照，本数据集的 `route_plan` 与 `tool_calls` 可以直接转成评测样本。
3. **回归重放**：改动 `UserProxy._route_for` 的路由表、`tools/schemas.py` 的参数模型或 `risk/rules.py` 的规则后，重新执行本数据集，比对 `intent`、`route_plan`、工具序列、`critic.verdict` 是否发生漂移。

## 规模

生产目标是 30000 条，拆分写在 `finagent/data_pipeline/sft_generation/plans.py` 的 `DEFAULT_TRAJECTORY_SCENARIOS`：

- `single_tool_call`：10000 条，意图族 `quote_or_metric_lookup`
- `multi_tool_call`：10000 条，意图族 `macro_micro_portfolio_impact`
- `critic_rewrite`：5000 条，意图族 `compliance_and_risk_rewrite`
- `interruption_recovery`：5000 条，意图族 `task_stack_and_resume`

当前交付 `data/finagent/finagent_tool_calling_seed20.jsonl` 共 20 条，四类场景各 5 条，用于格式确认与人工检查。实测长度：最短 1145 token，平均 1480 token，最长 2750 token（按 `builders._estimate_tokens` 的口径估算）。

## 样本字段

每条记录是 JSONL 中的一行，字段如下。

- `id`：样本标识，格式 `finagent-seed-NNN`
- `dataset_version`：数据集版本，当前 `seed20-v1`
- `scenario_kind`：`single_tool_call`、`multi_tool_call`、`critic_rewrite`、`interruption_recovery` 之一
- `task_instruction`：当前轮的用户任务指令原文，与 `messages` 中最后一条 `user` 内容一致
- `intent`：`IntentType` 的取值，来自 `LightweightIntentClassifier.classify`
- `intent_confidence`：意图置信度，来自同一分类器
- `route_plan`：`RouteStep` 列表，每项含 `node`、`reason`、`tools`、`required`，来自 `UserProxy._route_for`
- `interruption`：中断信息，含 `interrupted_task_id`、`new_intent`、`reason`，未触发时为 `null`
- `tool_calls`：工具调用明细，字段见下
- `critic`：风控审核结果，含 `verdict`、`flags`、`rewrite_suggestion`、`self_reflection`
- `final`：最终结果，含 `answer`、`sources`、`risk_disclaimer`、`status`
- `resumed_task`：被恢复的旧任务，含 `task_id`、`intent`、`description`、`checkpoint_id`，未触发时为 `null`
- `provenance`：生成来源，含 `runtime_mode`、`data_provider`、`orchestrator`、`candidate_authoring`、`answer_grounding`、`note`
- `messages`：ShareGPT 对话序列，训练时直接使用

`tool_calls` 每一项的字段：

- `tool_call_id`：调用标识
- `agent`：发起调用的 agent，取值来自 `AGENT_EVENT_NODES`，即 `macro_agent`、`quant_agent`、`report_agent`、`market_agent`、`memory_agent`、`router`
- `step_id`：当前路由步骤标识
- `tool_name`：工具名，必须在 `build_default_registry` 注册的 14 个工具之内
- `arguments`：调用参数，必须通过对应 `ToolInput` 子类的模型校验
- `status`：`success` 或 `error`
- `error`：失败原因，成功时为 `null`
- `result`：`ToolResult` 的完整序列化结果，含 `data`、`sources`、`source_ts`、`latency_ms`

## 轨迹格式规范

### 文件格式

JSONL，一行一条记录，UTF-8 编码，`ensure_ascii=False`。文件名与 `data/finagent/dataset_info.json` 中注册的 `sharegpt` 格式配合使用，`columns.messages` 指向 `messages` 字段。

### messages 序列

顺序固定为：

1. `system`：`CandidateResponseBuilder._system_prompt()` 的原文，追加可用工具清单与调用格式说明。工具清单由 `build_default_registry` 的 `ToolSpec` 生成，参数签名取自 `input_model.model_fields`。
2. 历史轮次：`user` / `assistant` 交替，来自 `history` 字段，仅 `interruption_recovery` 场景存在。
3. `user`：当前任务指令。
4. 工具交互对：每个工具调用一条 `assistant` 加一条 `tool`，按真实执行顺序排列。
5. `assistant`：最终答复，取自 `final.answer`。

### 工具调用写法

`assistant` 消息内容只包含调用块：

```
<tool_call>{"name": "get_realtime_stock", "arguments": {"ticker": "AAPL", "market": "US"}}</tool_call>
```

正则 `TOOL_CALL_RE` 在 `finagent/data_pipeline/cleaning/trajectory.py` 中定义，`canonicalize_tool_call` 负责别名归一：`get_macro_indicator` 归一为 `macro_indicator`，`search_research_reports` 归一为 `web_search`，`fetch_sec_filings` 的 `year` 归一为 `fiscal_year`。

### 工具观察写法

`tool` 消息内容是一个 JSON 对象：

```json
{
  "tool": "get_realtime_stock",
  "status": "success",
  "data": {"ticker": "AAPL", "market": "US", "price": 193.42, "currency": "USD", "exchange": "NASDAQ", "change_percent": 0.74},
  "sources": [{"source_type": "test_data", "title": "AAPL realtime quote", "freshness": "realtime"}],
  "error": null
}
```

完整 `SourceRef` 保留在顶层 `tool_calls[].result.sources`，`messages` 内只保留 `source_type`、`title`、`freshness` 三项，控制长度。

### 损失掩码

`MASKED_LOSS_ROLES = {"system", "user", "tool"}`，只有 `assistant` 消息参与损失计算。工具观察不参与损失，避免模型学习回放工具返回值。

### 长度上限

- 单工具样本不超过 2048 token
- 多工具样本不超过 4096 token

当前训练配置的 `cutoff_len: 2048` 会截断 4 条多工具样本（长度 2115 到 2750），训练前需要把 `cutoff_len` 调整到 4096，或对多工具样本单独分组打包。

## 质量校验标准

### 硬性标准

1. `python -m finagent.data_pipeline.cleaning.validate_dataset <file>` 返回 `invalid = 0`，`issues` 为空。
2. `messages` 首条为 `system`，末条为 `assistant`，至少一条 `user`，至少一条 `assistant`。
3. 每个 `<tool_call>` 的 `name` 在注册表内，`arguments` 通过对应 `ToolInput` 模型校验。
4. 每条 `tool` 观察前面必须是 `assistant` 或 `tool`，不允许孤立观察。
5. `intent` 与 `task_instruction` 一致：用 `LightweightIntentClassifier` 重新分类，结果必须相同。
6. `route_plan` 与 `UserProxy._route_for(intent, task_instruction)` 的输出逐项相同。
7. `final.status` 与 `critic.verdict` 对应：`reject` 对应 `risk_rejected`，`clarify` 对应 `needs_clarification`，`pass` 或 `rewrite` 对应 `completed`。
8. 答复中出现的数值必须能在 `tool_calls[].result.data` 中找到同源字段，生成脚本用绑定渲染并在缺字段时直接崩溃。
9. `scenario_kind` 与工具数量自洽：`single_tool_call` 的业务工具为 1 个，`multi_tool_call` 的业务工具至少 2 个，`compliance_rule_check` 不计入业务工具。

### 人工检查标准

- 答复中的数字与单位同工具结果一致，币种标注正确。
- 答复没有出现确定性收益承诺、满仓指令、杠杆指令。
- 拒答场景的措辞与 `risk/rules.py` 的 `safe_response` 一致，改写场景与 `rewrite_response` 一致。
- 每条样本的 `provenance.note` 说明该条覆盖的行为路径。

### 已知边界

- `InMemoryMarketDataProvider` 生成的 20 个价格点单调上升，`max_drawdown` 恒为 0，`volatility` 与 `sharpe` 读数失真。样本不引用这三项数值，答复中明说读数接近零、需要更长区间复核。
- `get_delayed_quote` 只在 `get_realtime_stock` 超时时作为降级工具触发，本批 20 条未覆盖，属于第二批补充项。
- 候选答复由人工撰写，`provenance.candidate_authoring` 标记为 `human_reviewed`；工具调用、观察、路由、风险判定由项目代码实际执行产生。
- `tool_call_id`、`source_id`、`latency_ms`、`source_ts` 是运行期生成值，不参与语义，重新生成时会变化。

## 重新生成与校验

```
cd "/d/md/AI实习/project/finagent"
uv run python -m finagent.data_pipeline.sft_generation.seed_trajectories
uv run python -m finagent.data_pipeline.cleaning.validate_dataset data/finagent/finagent_tool_calling_seed20.jsonl
```

生成脚本把意图、路由、工具调用、工具观察、风控审核、最终答复全部走项目真实代码路径；意图或最终状态与预期不符时直接抛错，不写入文件。

## 接入训练

在 `data/finagent/dataset_info.json` 中新增一条记录，`formatting` 与 `columns` 沿用现有 `finagent_tool_calling_30k` 条目，`file_name` 指向 `finagent_tool_calling_seed20.jsonl`，训练配置的 `dataset` 字段改成该键名即可。种子集只用于格式确认与小样本过拟合检查，正式训练使用 30000 条全量数据。

