import unittest
from unittest.mock import MagicMock

from text_to_sql.agents.planner_node import parse_planner_output, planner_node_with_fallback
from text_to_sql.agents.state import build_initial_state


class TestParsePlannerOutput(unittest.TestCase):
    def test_parse_full_output(self):
        text = """
语义改写：查询用户数量
业务知识摘要：用户定义为注册用户
执行计划：
1. 确定主表与关联表：users
2. 过滤条件：active = 1
3. 聚合与分组策略：COUNT(*)
4. 排序与限制：无
5. 边界情况与注意事项：注意空值
警告：
- 缺少时间范围
- 存在歧义
"""
        result = parse_planner_output(text)
        self.assertEqual(result["semantic_rewrite"], "查询用户数量")
        self.assertEqual(result["business_knowledge"], "用户定义为注册用户")
        self.assertIn("1. 确定主表", result["execution_plan"])
        self.assertEqual(result["warnings"], ["缺少时间范围", "存在歧义"])

    def test_parse_json_output(self):
        text = """
```json
{
  "semantic_rewrite": "查询订单 GMV",
  "business_knowledge": "GMV = 支付金额",
  "execution_plan": "1. 确定主表：orders",
  "warnings": ["无时间范围"]
}
```
"""
        result = parse_planner_output(text)
        self.assertEqual(result["semantic_rewrite"], "查询订单 GMV")
        self.assertEqual(result["warnings"], ["无时间范围"])

    def test_parse_empty_output(self):
        result = parse_planner_output("")
        self.assertEqual(result["semantic_rewrite"], "")
        self.assertEqual(result["warnings"], [])

    def test_parse_partial_output(self):
        text = "语义改写：查询订单\n业务知识摘要：订单包含退款"
        result = parse_planner_output(text)
        self.assertEqual(result["semantic_rewrite"], "查询订单")
        self.assertEqual(result["business_knowledge"], "订单包含退款")
        self.assertEqual(result["execution_plan"], "")

    def test_unstructured_output_is_not_treated_as_a_plan(self):
        result = parse_planner_output("I cannot produce a plan")

        self.assertEqual(result["execution_plan"], "")

    def test_parse_markdown_headings_and_strip_sql_from_plan(self):
        text = """
语义改写：查询已支付订单金额

### 业务知识摘要：
无

### 执行计划：
1. 主表为 orders。
2. 过滤 status = 'paid'。
3. 返回 amount 和 created_at 明细。

### SQL 查询：
```sql
SELECT amount, created_at FROM orders WHERE status = 'paid';
```

警告：无
"""
        result = parse_planner_output(text)
        self.assertEqual(result["semantic_rewrite"], "查询已支付订单金额")
        self.assertEqual(result["business_knowledge"], "无")
        self.assertIn("主表为 orders", result["execution_plan"])
        self.assertNotIn("SELECT", result["execution_plan"])

    def test_fallback_can_be_disabled(self):
        llm = MagicMock()
        llm.invoke.side_effect = RuntimeError("planner offline")
        retriever = MagicMock()
        retriever.retrieve_tables.return_value = ["users"]
        retriever.retrieve_columns.return_value = ["users.id"]
        collector = MagicMock()
        collector.bloodline_completion.return_value = ["users"]
        collector.get_compressed_schema.return_value = "Table users"
        cache = MagicMock()
        cache.get.return_value = None

        with self.assertRaisesRegex(RuntimeError, "planner offline"):
            planner_node_with_fallback(
                build_initial_state("查询用户"),
                llm=llm,
                schema_collector=collector,
                schema_retriever=retriever,
                business_kb=MagicMock(search=MagicMock(return_value="无")),
                entity_linker=MagicMock(lookup_values=MagicMock(return_value=[])),
                semantic_cache=cache,
                fallback_enabled=False,
            )

    def test_invalid_planner_output_uses_fallback(self):
        llm = MagicMock()
        llm.invoke.return_value = "not a structured planner response"
        retriever = MagicMock()
        retriever.retrieve_tables.return_value = ["users"]
        retriever.retrieve_columns.return_value = ["users.id"]
        collector = MagicMock()
        collector.schema_version = "v1"
        collector.get_all_table_names.return_value = ["users"]
        collector.bloodline_completion.return_value = ["users"]
        collector.get_compressed_schema.return_value = "Table users"
        cache = MagicMock()
        cache.get.return_value = None

        result = planner_node_with_fallback(
            build_initial_state("查询用户"),
            llm=llm,
            schema_collector=collector,
            schema_retriever=retriever,
            business_kb=MagicMock(search=MagicMock(return_value="无")),
            entity_linker=MagicMock(lookup_values=MagicMock(return_value=[])),
            semantic_cache=cache,
        )

        self.assertTrue(result["fallback"])
        self.assertIn("missing a structured execution plan", result["error_msg"])


if __name__ == "__main__":
    unittest.main()
