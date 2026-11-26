"""
Prompt templates and formatting helpers.
"""

PLANNER_PROMPT = """你是一个资深的数据库架构师。请根据用户问题、业务知识、值映射和表结构，制定 SQL 查询逻辑步骤。

【用户问题】
{query}

【检索到的业务知识】
{business_knowledge}

【检索到的相关表及压缩结构】
{compressed_schema}

【检索到的值映射】
{value_mappings}

【数据库方言】
{dialect}

【方言特殊规则】
{dialect_rules}

【意图约束】
1. 不要添加用户没有明确提出的过滤条件。除非用户问题、值映射或业务知识明确要求，否则不要自行添加 status='paid'、active=1、amount>=0、时间范围等条件。
2. “查询/列出/查看 X 的字段”默认是明细查询，直接返回用户要求的字段；只有出现“统计、总和、合计、汇总、平均、数量、个数、最大、最小、排名、占比、率”等明确聚合词时，才设计聚合、GROUP BY、SUM/COUNT/AVG/MIN/MAX。
3. “查询已支付订单的金额和创建时间”这类问题是明细查询：过滤已支付订单后返回 amount、created_at，不要改写成 SUM(amount)、MIN(created_at)。
4. 如果业务知识与用户问题冲突，以用户问题为准；可在警告中提示冲突，不要直接改变查询口径。

请严格按以下字段输出，不要直接写完整 SQL：
语义改写：将口语化查询改写为标准数据查询描述
业务知识摘要：列出会影响 SQL 逻辑的业务口径
执行计划：
1. 确定主表与关联表：...
2. 过滤条件：...
3. 聚合与分组策略：...
4. 排序与限制：...
5. 边界情况与注意事项：...
警告：如缺少关键条件、存在歧义或口径冲突，请逐条列出；没有则写“无”
"""


CODER_PROMPT = """你是一个资深的数据库工程师。请根据给定表结构和执行计划，为用户需求编写一条只读 SQL。

【表结构】
{schema}

【用户需求】
{query}

【执行计划】
{plan}

【业务知识】
{business_knowledge}

【数据库方言】
{dialect}

【方言特殊规则】
{dialect_rules}

【值映射】
{value_mappings}

【要求】
1. 只输出一条 SELECT、WITH 或 EXPLAIN 开头的只读 SQL。
2. 可以在 <think>...</think> 中写简短推理，但 </think> 后只能输出纯 SQL。
3. 不要输出 INSERT、UPDATE、DELETE、CREATE、DROP、ALTER、TRUNCATE。
4. SQL 必须符合 {dialect} 方言。
5. 严格服从用户原始需求：不要添加用户没有明确提出的 status、active、amount、时间等过滤条件。
6. 明细查询不要聚合；只有用户明确要求统计、总和、合计、汇总、平均、数量、个数、最大、最小、排名、占比、率时，才使用 GROUP BY 或 SUM/COUNT/AVG/MIN/MAX。
7. 如果用户说“查询已支付订单的金额和创建时间”，应返回每条已支付订单的 amount、created_at 明细，不要写成 SUM(amount)、MIN(created_at)。

输出格式要求：如果包含 <think>，</think> 后只能保留一条纯 SQL；最终答案不得包含解释、Markdown 或多条 SQL。
"""


REPAIR_PROMPT = """你是一个数据库 SQL 排错专家。系统执行候选 SQL 时失败，请根据错误历史修复 SQL。

【用户原始问题】
{query}

【数据库方言】
{dialect}

【方言特殊规则】
{dialect_rules}

【表结构】
{schema}

【执行计划】
{plan}

【值映射】
{value_mappings}

【历史错误记录】
{error_history_text}

【要求】
1. 只输出一条修复后的 SELECT、WITH 或 EXPLAIN 开头的只读 SQL。
2. 可以在 <think>...</think> 中说明错误原因，但 </think> 后只能输出纯 SQL。
3. 不要重复已经失败的错误写法。
4. 修复只能解决字段名、表名、方言、语法、连接条件等执行错误；不要改变用户原始语义，不要新增用户未要求的过滤条件或聚合。
5. 如果错误历史提示“Query asks for detail fields, but SQL uses aggregation”，必须改为明细查询，去掉 GROUP BY 和 SUM/COUNT/AVG/MIN/MAX。
6. 如果错误历史提示“SQL adds status='...' filter”，除非用户原始问题明确包含该状态，否则必须移除这个状态过滤。

输出格式要求：如果包含 <think>，</think> 后只能保留一条修复后的纯 SQL；最终答案不得包含解释、Markdown 或多条 SQL。
"""


def build_error_history_text(error_history: list) -> str:
    """Build readable retry history text for the repair prompt."""

    if not error_history:
        return "无历史错误"

    lines = []
    for entry in error_history:
        retry_num = entry.get("retry", 0) + 1
        lines.append(f"第 {retry_num} 轮尝试")
        for err in entry.get("errors", []):
            sql = (err.get("sql", "") or "")[:500]
            error_msg = err.get("error", "")
            stage = err.get("stage", "")
            lines.append(f"  - SQL: {sql}")
            lines.append(f"    错误: {error_msg}")
            lines.append(f"    阶段: {stage}")

    return "\n".join(lines)


def format_execution_plan(planner_output: dict) -> str:
    """Format Planner output into text consumed by Coder."""

    if not planner_output:
        return "无执行计划"

    lines = []
    execution_plan = planner_output.get("execution_plan", "")
    if execution_plan:
        lines.append(execution_plan)

    semantic_rewrite = planner_output.get("semantic_rewrite", "")
    if semantic_rewrite:
        lines.append(f"语义改写: {semantic_rewrite}")

    business_knowledge = planner_output.get("business_knowledge", "")
    if business_knowledge:
        lines.append(f"业务知识摘要: {business_knowledge}")

    warnings = planner_output.get("warnings", [])
    if warnings:
        lines.append(f"警告: {'; '.join(warnings)}")

    return "\n".join(lines) if lines else "无执行计划"
