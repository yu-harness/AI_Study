"""
Self-consistency selector for valid SQL candidates.
"""

import hashlib
import json
import re
from typing import List


class ConsistencySelector:
    """Majority voting by result signature, with optional LLM-as-a-judge tie break."""

    def __init__(self, judge_llm=None):
        self.judge_llm = judge_llm

    def select_best(self, sqls: List[str], query: str, sandbox, dialect: str = "mysql") -> str:
        """Select the best SQL from already validated candidates."""

        if not sqls:
            return ""
        if len(sqls) == 1:
            return sqls[0]

        signatures = []
        for sql in sqls:
            result = self._execute_candidate(sandbox, sql, dialect)
            if result.get("success"):
                signatures.append((sql, self._result_signature(result.get("data", []))))

        if not signatures:
            return self._rule_based_select(sqls)

        vote_groups = {}
        for sql, signature in signatures:
            vote_groups.setdefault(signature, []).append(sql)

        groups = sorted(vote_groups.values(), key=len, reverse=True)
        best_group = groups[0]
        has_unique_majority = len(groups) == 1 or len(best_group) > len(groups[1])
        if not has_unique_majority:
            tied_sqls = [sql for group in groups if len(group) == len(best_group) for sql in group]
            return self._judge_or_rule_select(tied_sqls, query)

        return self._judge_or_rule_select(best_group, query)

    @staticmethod
    def _execute_candidate(sandbox, sql: str, dialect: str) -> dict:
        try:
            return sandbox.execute(sql, dialect=dialect, limit=10)
        except TypeError:
            return sandbox.execute(sql, limit=10)

    @staticmethod
    def _result_signature(rows: list) -> str:
        """Create a stable signature from result columns and the first rows."""

        sample = rows[:3]
        columns = sorted(sample[0].keys()) if sample and isinstance(sample[0], dict) else []
        payload = json.dumps({"columns": columns, "rows": sample}, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _rule_based_select(sqls: List[str]) -> str:
        def score(sql: str) -> tuple:
            upper = sql.upper()
            has_where = " WHERE " in f" {upper} "
            avoids_select_star = "SELECT *" not in upper
            return (not has_where, not avoids_select_star, len(sql))

        return min(sqls, key=score)

    def _judge_or_rule_select(self, sqls: List[str], query: str) -> str:
        if len(sqls) == 1:
            return sqls[0]
        if self.judge_llm:
            return self._llm_judge(sqls, query)
        return self._rule_based_select(sqls)

    def _llm_judge(self, sqls: List[str], query: str) -> str:
        prompt = "你是 SQL 评审专家。请从候选 SQL 中选择最能回答用户问题的一条，只输出编号。\n"
        prompt += f"用户问题：{query}\n\n候选 SQL：\n"
        for idx, sql in enumerate(sqls, 1):
            prompt += f"{idx}. {sql}\n"

        response = self._invoke_judge(prompt)
        match = re.search(r"\d+", response or "")
        idx = int(match.group()) - 1 if match else 0
        return sqls[max(0, min(idx, len(sqls) - 1))]

    def _invoke_judge(self, prompt: str) -> str:
        if hasattr(self.judge_llm, "invoke"):
            result = self.judge_llm.invoke(prompt)
            return getattr(result, "content", str(result))

        if hasattr(self.judge_llm, "generate"):
            from vllm import SamplingParams

            params = SamplingParams(temperature=0.1, max_tokens=32)
            outputs = self.judge_llm.generate([prompt], params)
            if outputs and outputs[0].outputs:
                return outputs[0].outputs[0].text
            return ""

        return str(self.judge_llm(prompt))
