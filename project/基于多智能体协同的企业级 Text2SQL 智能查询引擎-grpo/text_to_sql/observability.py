"""Structured logging and Prometheus metrics for Text2SQL."""

import logging

import structlog
from prometheus_client import Counter, Histogram


QUERY_REQUESTS = Counter(
    "text2sql_query_requests_total",
    "Text2SQL query requests by outcome.",
    ("status", "cached", "fallback"),
)
QUERY_LATENCY = Histogram(
    "text2sql_query_latency_seconds",
    "End-to-end Text2SQL query latency.",
    buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300),
)
MODEL_LATENCY = Histogram(
    "text2sql_model_latency_seconds",
    "Ollama generation latency by model.",
    ("model",),
    buckets=(0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300),
)
MODEL_TOKENS = Counter(
    "text2sql_model_tokens_total",
    "Ollama prompt and completion tokens by model.",
    ("model", "direction"),
)


def configure_logging(level: int = logging.INFO):
    """Configure JSON output for both structlog and standard-library loggers."""

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
