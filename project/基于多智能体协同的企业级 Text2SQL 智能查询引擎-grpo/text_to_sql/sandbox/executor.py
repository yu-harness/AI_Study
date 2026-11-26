"""
Sandbox SQL validator and executor.
"""

from typing import List
from .connection_pool import SandboxConnectionPool
from .security import get_security_checker


class SandboxExecutor:
    """Validate SQL safety and cost before executing it in the sandbox."""

    def __init__(self, pool: SandboxConnectionPool, cost_threshold: int = 10_000_000):
        self.pool = pool
        self.cost_threshold = cost_threshold
        self.security_checker = get_security_checker()

    def validate(self, sql: str, dialect: str = "mysql") -> tuple:
        """Return (is_valid, error, details)."""

        security = self.security_checker.check(sql)
        checks = [{"stage": "security", "success": security["safe"], "output": security}]
        if not security["safe"]:
            return False, security["reason"], {
                "stage": "security",
                "matched_pattern": security["matched_pattern"],
                "checks": checks,
            }

        explain_result = self.pool.explain(sql, dialect)
        compact_explain = {
            key: value
            for key, value in explain_result.items()
            if key != "plan"
        }
        if "plan" in explain_result:
            compact_explain["plan"] = [str(row) for row in explain_result.get("plan", [])[:5]]
        checks.append(
            {
                "stage": "explain",
                "success": explain_result.get("success", False),
                "output": compact_explain,
            }
        )
        if not explain_result.get("success"):
            return False, explain_result.get("error", "EXPLAIN failed"), {
                "stage": "explain",
                "checks": checks,
            }

        estimated_rows = explain_result.get("estimated_rows", 0) or 0
        cost_ok = estimated_rows <= self.cost_threshold
        checks.append(
            {
                "stage": "cost",
                "success": cost_ok,
                "output": {
                    "estimated_rows": estimated_rows,
                    "cost_threshold": self.cost_threshold,
                    "estimated_cost": explain_result.get("estimated_cost"),
                },
            }
        )
        if estimated_rows > self.cost_threshold:
            return False, f"Estimated rows ({estimated_rows}) exceeds threshold", {
                "stage": "cost",
                "estimated_rows": estimated_rows,
                "checks": checks,
            }

        return True, "", {
            "stage": "validated",
            "estimated_rows": estimated_rows,
            "estimated_cost": explain_result.get("estimated_cost"),
            "checks": checks,
        }

    def execute(self, sql: str, dialect: str = "mysql", limit: int = 1) -> dict:
        """Execute SQL with a small default result limit."""

        security = self.security_checker.check(sql)
        if not security["safe"]:
            return {
                "success": False,
                "error": security["reason"],
                "details": {
                    "stage": "security",
                    "matched_pattern": security["matched_pattern"],
                },
                "data": [],
                "row_count": 0,
            }
        return self.pool.execute(sql, limit=limit)

    def execute_and_validate(self, sql: str, dialect: str = "mysql") -> tuple:
        """Validate then execute SQL."""

        is_valid, error, details = self.validate(sql, dialect)
        if not is_valid:
            return False, {"success": False, "error": error, "details": details}

        result = self.execute(sql, dialect)
        return result.get("success", False), result


def select_best_sql(sqls: List[str], query: str = "") -> str:
    """Simple deterministic fallback selector for valid SQLs."""

    if not sqls:
        return ""
    if len(sqls) == 1:
        return sqls[0]

    def score_sql(sql: str) -> tuple:
        upper = sql.upper()
        has_where = " WHERE " in f" {upper} "
        avoids_select_star = "SELECT *" not in upper
        return (not has_where, not avoids_select_star, len(sql))

    return min(sqls, key=score_sql)
