import unittest

from text_to_sql.agents.prompts import (
    CODER_PROMPT,
    PLANNER_PROMPT,
    REPAIR_PROMPT,
    build_error_history_text,
    format_execution_plan,
)


class TestBuildErrorHistoryText(unittest.TestCase):
    def test_empty_history(self):
        self.assertEqual(build_error_history_text([]), "无历史错误")

    def test_single_error(self):
        history = [
            {
                "retry": 0,
                "errors": [
                    {"sql": "SELECT * FROM users", "error": "Table not found", "stage": "execution"}
                ],
            }
        ]
        result = build_error_history_text(history)
        self.assertIn("第 1 轮尝试", result)
        self.assertIn("SELECT * FROM users", result)
        self.assertIn("Table not found", result)
        self.assertIn("execution", result)

    def test_multiple_errors(self):
        history = [
            {
                "retry": 1,
                "errors": [
                    {"sql": "SELECT a FROM t", "error": "err1", "stage": "explain"},
                    {"sql": "SELECT b FROM t", "error": "err2", "stage": "execution"},
                ],
            }
        ]
        result = build_error_history_text(history)
        self.assertIn("第 2 轮尝试", result)
        self.assertIn("err1", result)
        self.assertIn("err2", result)


class TestFormatExecutionPlan(unittest.TestCase):
    def test_empty_plan(self):
        self.assertEqual(format_execution_plan({}), "无执行计划")

    def test_full_plan(self):
        planner_output = {
            "execution_plan": "1. 确定主表与关联表：users",
            "semantic_rewrite": "查询用户数量",
            "business_knowledge": "用户定义为注册用户",
            "warnings": ["缺少时间范围", "存在歧义"],
        }
        result = format_execution_plan(planner_output)
        self.assertIn("1. 确定主表", result)
        self.assertIn("语义改写: 查询用户数量", result)
        self.assertIn("业务知识摘要: 用户定义为注册用户", result)
        self.assertIn("缺少时间范围", result)


class TestPromptIntentGuardrails(unittest.TestCase):
    def test_planner_blocks_unrequested_filters(self):
        self.assertIn("不要添加用户没有明确提出的过滤条件", PLANNER_PROMPT)

    def test_coder_blocks_aggregation_for_detail_queries(self):
        self.assertIn("明细查询不要聚合", CODER_PROMPT)

    def test_repair_preserves_original_semantics(self):
        self.assertIn("不要新增用户未要求的过滤条件或聚合", REPAIR_PROMPT)


if __name__ == "__main__":
    unittest.main()
