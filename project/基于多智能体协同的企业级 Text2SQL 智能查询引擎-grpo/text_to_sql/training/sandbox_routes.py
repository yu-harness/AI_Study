"""Shared database routing and executor construction for GRPO training."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Mapping

from sqlalchemy.engine import make_url

from text_to_sql.sandbox.connection_pool import SandboxConnectionPool
from text_to_sql.sandbox.executor import SandboxExecutor


SUPPORTED_TRAINING_DIALECTS = frozenset({"mysql", "postgresql", "sqlite", "oracle"})


def normalize_database_dialect(dialect: str) -> str:
    """Normalize driver-qualified database dialect names."""

    backend = (dialect or "").strip().lower().split("+", 1)[0]
    return "postgresql" if backend in {"postgres", "postgresql"} else backend


def sqlglot_dialect(dialect: str) -> str:
    """Return the sqlglot name for one supported database dialect."""

    normalized = normalize_database_dialect(dialect)
    return "postgres" if normalized == "postgresql" else normalized


def select_sandbox_route(
    sandbox_db_urls: str | Mapping[str, str],
    target_db: str,
) -> tuple[str, str]:
    """Resolve one target database URL and derive its authoritative dialect."""

    if not target_db:
        raise ValueError("GRPO sample requires target_db for sandbox routing")
    routes = json.loads(sandbox_db_urls) if isinstance(sandbox_db_urls, str) else sandbox_db_urls
    if not isinstance(routes, Mapping):
        raise ValueError("TEXT2SQL_TRAINING_DB_URLS must be a JSON object")
    db_url = routes.get(target_db)
    if not isinstance(db_url, str) or not db_url.strip():
        raise ValueError(f"No training sandbox URL configured for target_db={target_db}")
    dialect = normalize_database_dialect(make_url(db_url).get_backend_name())
    if dialect not in SUPPORTED_TRAINING_DIALECTS:
        raise ValueError(f"Unsupported training sandbox dialect: {dialect}")
    return db_url, dialect


@lru_cache(maxsize=8)
def build_training_executor(
    sandbox_db_url: str,
    redis_url: str,
    query_timeout: int,
    cost_threshold_rows: int,
) -> SandboxExecutor:
    """Build one cached sandbox executor per routed training database."""

    if not sandbox_db_url:
        raise ValueError("Training sandbox database URL must be configured")
    if not redis_url:
        raise ValueError("TEXT2SQL_REDIS_URL must be configured")
    pool = SandboxConnectionPool(
        db_url=sandbox_db_url,
        redis_url=redis_url,
        query_timeout=query_timeout,
    )
    return SandboxExecutor(pool, cost_threshold=cost_threshold_rows)
