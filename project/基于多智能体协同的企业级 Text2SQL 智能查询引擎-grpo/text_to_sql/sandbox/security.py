"""
Read-only SQL security checks for sandbox execution.
"""

import re
from typing import List


DANGEROUS_PATTERNS = [
    r"\bDROP\s+(TABLE|DATABASE|INDEX|VIEW)\b",
    r"\bDELETE\s+FROM\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bALTER\s+TABLE\b",
    r"\bINSERT\s+INTO\b",
    r"\bUPDATE\b.*\bSET\b",
    r"\bCREATE\s+(TABLE|INDEX|VIEW|DATABASE)\b",
    r"\bEXEC\s*\(",
    r"\bINTO\s+(OUTFILE|DUMPFILE)\b",
    r"\bLOAD_FILE\s*\(",
    r"\bPG_(READ|WRITE)_FILE\s*\(",
    r"\bCOPY\b.*\b(TO|FROM)\b",
    r"--",
    r"/\*",
    r";\s*\w+",
]

SAFE_PREFIXES = [
    r"^\s*SELECT\s+",
    r"^\s*WITH\s+",
    r"^\s*EXPLAIN\s+",
]


class SQLSecurityChecker:
    """Validate that a SQL string is a single read-only statement."""

    def __init__(self, custom_blacklist: List[str] = None):
        self.patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in DANGEROUS_PATTERNS]
        if custom_blacklist:
            self.patterns.extend(
                [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in custom_blacklist]
            )
        self.safe_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in SAFE_PREFIXES]

    def check(self, sql: str) -> dict:
        """Return structured security-check details."""

        if not sql or not sql.strip():
            return {
                "safe": False,
                "reason": "SQL must not be empty",
                "matched_pattern": "EMPTY_SQL",
            }

        if not any(pattern.match(sql) for pattern in self.safe_patterns):
            return {
                "safe": False,
                "reason": "SQL must start with SELECT/WITH/EXPLAIN",
                "matched_pattern": "INVALID_PREFIX",
            }

        inspect_sql = self._mask_quoted_literals(sql)
        for pattern in self.patterns:
            match = pattern.search(inspect_sql)
            if match:
                return {
                    "safe": False,
                    "reason": f"Detected forbidden SQL fragment: {match.group()}",
                    "matched_pattern": pattern.pattern,
                }

        if not self._check_quote_balance(sql):
            return {
                "safe": False,
                "reason": "Quotes or parentheses are not balanced",
                "matched_pattern": "QUOTE_IMBALANCE",
            }

        return {"safe": True, "reason": "", "matched_pattern": ""}

    @staticmethod
    def _mask_quoted_literals(sql: str) -> str:
        """Replace quoted literal content so keyword checks only inspect SQL structure."""

        chars = list(sql)
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(chars):
            ch = chars[i]
            if ch == "'" and not in_double_quote:
                if in_single_quote and i + 1 < len(chars) and chars[i + 1] == "'":
                    chars[i + 1] = " "
                    i += 2
                    continue
                in_single_quote = not in_single_quote
            elif ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif in_single_quote or in_double_quote:
                chars[i] = " "
            i += 1
        return "".join(chars)

    def _check_quote_balance(self, sql: str) -> bool:
        """Check single quotes, double quotes, and parentheses."""

        stack = []
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(sql):
            ch = sql[i]
            if ch == "'" and not in_double_quote:
                if in_single_quote and i + 1 < len(sql) and sql[i + 1] == "'":
                    i += 2
                    continue
                in_single_quote = not in_single_quote
            elif ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote:
                if ch == "(":
                    stack.append(ch)
                elif ch == ")":
                    if not stack:
                        return False
                    stack.pop()
            i += 1

        return not in_single_quote and not in_double_quote and not stack


_checker = None


def get_security_checker(custom_blacklist: List[str] = None) -> SQLSecurityChecker:
    """Return the process-wide SQL security checker."""

    global _checker
    if _checker is None or custom_blacklist:
        return SQLSecurityChecker(custom_blacklist) if custom_blacklist else _init_default_checker()
    return _checker


def _init_default_checker() -> SQLSecurityChecker:
    global _checker
    _checker = SQLSecurityChecker()
    return _checker


def security_check(sql: str) -> bool:
    """Return True when SQL is unsafe."""

    return not get_security_checker().check(sql)["safe"]
