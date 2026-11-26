"""
Heuristic fallback planner used when the large Planner model is unavailable.
"""

import jieba


class FallbackPlanner:
    """Small rule-based fallback for table and value discovery."""

    def __init__(self, schema_collector, entity_linker):
        self.schema_collector = schema_collector
        self.entity_linker = entity_linker

    def heuristic_parse(self, query: str) -> dict:
        """Extract candidate tables and values with simple lexical matching."""

        tokens = list(jieba.cut(query))
        value_mappings = self.entity_linker.lookup_values(query)

        all_tables = self.schema_collector.get_all_table_names()
        matched_tables = [
            table
            for table in all_tables
            if any(token and (table in token or token in table) for token in tokens)
        ]

        if not matched_tables:
            matched_tables = self.schema_collector.get_hot_tables(top_k=5)

        return {
            "semantic_rewrite": query,
            "business_knowledge": "无，Agent1 降级模式",
            "execution_plan": "基于关键词和值映射自动关联候选表，缺少大模型生成的详细执行计划。",
            "warnings": ["Agent1 异常，使用启发式解析兜底"],
            "candidate_tables": matched_tables,
            "value_mappings": value_mappings,
            "dialect": "mysql",
            "fallback": True,
        }
