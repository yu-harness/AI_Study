# 完整示例：Tether 的长上下文治理

演示一条简历条目出题并同时给答案的写法，输出写入 `简历/简历八股.md` 的对应小节。

## 输入

> 简历条目：长上下文治理，五层输入配优先级预算裁剪，12 组配置下平均压缩率 25.11%，当前请求保留率 100%。

## 输出

### 长上下文治理

**问**：我看你简历上写了上下文按优先级做预算裁剪。我们线上跑一个代码助手，聊到第 30 轮的时候单次请求的 prompt 到了两万多字符，费用比第一轮高了七八倍。换成你这套裁剪，你会先把哪一段让出来？

**答**：顺序是相关记忆、过程历史、工作记忆、稳定背景，当前请求不参与。

依据是离当前任务主线有多远：相关记忆是按需补充的，先收；过程历史里多是旧过程，压掉不影响主线；工作记忆更贴近任务，晚一点动；稳定背景尽量保持稳定。代码里这个顺序是 `DEFAULT_REDUCTION_ORDER`，每次扣减量等于溢出量，每段有自己的下限，扣到下限就不再动；checkpoint 有独立预算，不在缩减序列里。

边界是预算按字符算，中文、英文、代码的字符与 token 比例不同，换语料就不准，也没法按模型上下文窗口自适应。

**问**：25.11% 是靠激进裁剪换来的吗？

**答**：不是，压缩率和保留率一起报。

12 组配置覆盖历史长度三档、记忆负载两档、请求长度两档，平均 prompt 从 8490.33 压到 6173.67 字符，平均压缩率 25.11%，最高 37.19%，最低 14.23%，当前请求保留率 100%。

保留率 100% 只证明最危险的那一项没被裁坏，不证明工作记忆和过程历史里的关键信息都还在，这一点我没有单独测。

## 查证记录

- 数字：`tether/benchmarks/results/resume-archive/context-ablation-v2.json`（summary.avg_raw_prompt_chars、avg_full_prompt_chars、avg_prompt_compression_ratio、max_prompt_compression_ratio、current_request_preserved_rate）。
- 机制：`tether/tether/context_manager.py`（DEFAULT_TOTAL_BUDGET、DEFAULT_SECTION_BUDGETS、DEFAULT_REDUCTION_ORDER、_compute_section_floors）。
- 口径问题：评测只输出字符数，模型计费按 token，两套口径没有换算，建议在评测输出里补 token 计数。
