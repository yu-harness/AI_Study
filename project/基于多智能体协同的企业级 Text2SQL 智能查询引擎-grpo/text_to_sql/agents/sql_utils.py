"""
Utilities for normalizing model output into executable SQL candidates.
"""

import re
from typing import Iterable, List


READONLY_SQL_PREFIX = re.compile(r"^\s*(SELECT|WITH|EXPLAIN)\b", re.IGNORECASE | re.DOTALL)
SQL_START = re.compile(
    r"\b(SELECT|WITH|EXPLAIN|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\b",
    re.IGNORECASE,
)


def strip_think_block(text: str) -> str:
    """Return text after the final </think> tag when present."""

    if not text:
        return ""
    marker = "</think>"
    idx = text.lower().rfind(marker)
    if idx == -1:
        return text.strip()
    return text[idx + len(marker) :].strip()


def extract_sql(text: str) -> str:
    """Extract the first SQL statement from LLM output.

    Supported model output shapes:
    - <think>...</think> SELECT ...
    - ```sql SELECT ... ```
    - plain SQL
    - prose followed by a SQL statement
    """

    if not text:
        return ""

    normalized = strip_think_block(text).strip()

    fenced = re.search(r"```(?:sql)?\s*(.*?)\s*```", normalized, re.IGNORECASE | re.DOTALL)
    if fenced:
        normalized = fenced.group(1).strip()

    start = SQL_START.search(normalized)
    if start:
        normalized = normalized[start.start() :].strip()

    normalized = re.sub(r"^SQL\s*[:：]\s*", "", normalized, flags=re.IGNORECASE).strip()
    normalized = _trim_after_first_statement(normalized)
    return normalized.strip()


def extract_readonly_sql(text: str) -> str:
    """Extract SQL and return it only when it starts with a read-only prefix."""

    sql = extract_sql(text)
    if not sql or not READONLY_SQL_PREFIX.match(sql):
        return ""
    return sql


def normalize_sql_candidates(outputs: Iterable[str]) -> List[str]:
    """Extract, filter, and de-duplicate read-only SQL candidates."""

    seen = set()
    sqls = []
    for output in outputs:
        sql = extract_readonly_sql(output)
        if not sql:
            continue
        key = re.sub(r"\s+", " ", sql).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        sqls.append(sql)
    return sqls


def _trim_after_first_statement(sql: str) -> str:
    """Keep one SQL statement while allowing a trailing semicolon."""

    in_single = False
    in_double = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and not in_double:
            if in_single and i + 1 < len(sql) and sql[i + 1] == "'":
                i += 2
                continue
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ";" and not in_single and not in_double:
            return sql[: i + 1]
        i += 1
    return sql
