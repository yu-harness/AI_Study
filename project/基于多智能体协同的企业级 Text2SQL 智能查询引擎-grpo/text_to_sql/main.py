"""
Main entry points for the Text2SQL system.
"""

import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from uuid import uuid4

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
import redis
import yaml

try:
    from .agents.state import build_initial_state
    from .agents.workflow import create_workflow, init_workflow
    from .agents.planner_node import planner_node_with_fallback
    from .agents.coder_node import coder_node
    from .agents.executor_node import executor_node
    from .agents.consistency_selector import ConsistencySelector
    from .agents.sql_utils import extract_sql as _extract_sql
    from .agents.debug_trace import append_trace
    from .llm.ollama_client import OllamaLLM, OllamaSamplingParams, list_ollama_models
    from .metadata.collector import SchemaCollector
    from .metadata.scheduler import start_scheduler, stop_scheduler
    from .retrieval.business_kb import BusinessKnowledgeBase
    from .retrieval.embeddings import create_embedding_model
    from .retrieval.schema_retriever import SchemaRetriever
    from .retrieval.router import SemanticRouter
    from .retrieval.entity_linker import EntityLinker
    from .cache.semantic_cache import SemanticCache
    from .sandbox.connection_pool import SandboxConnectionPool
    from .sandbox.executor import SandboxExecutor
    from .observability import QUERY_LATENCY, QUERY_REQUESTS, configure_logging
except ImportError:  # pragma: no cover - supports running python text_to_sql/main.py
    from agents.state import build_initial_state
    from agents.workflow import create_workflow, init_workflow
    from agents.planner_node import planner_node_with_fallback
    from agents.coder_node import coder_node
    from agents.executor_node import executor_node
    from agents.consistency_selector import ConsistencySelector
    from agents.sql_utils import extract_sql as _extract_sql
    from agents.debug_trace import append_trace
    from llm.ollama_client import OllamaLLM, OllamaSamplingParams, list_ollama_models
    from metadata.collector import SchemaCollector
    from metadata.scheduler import start_scheduler, stop_scheduler
    from retrieval.business_kb import BusinessKnowledgeBase
    from retrieval.embeddings import create_embedding_model
    from retrieval.schema_retriever import SchemaRetriever
    from retrieval.router import SemanticRouter
    from retrieval.entity_linker import EntityLinker
    from cache.semantic_cache import SemanticCache
    from sandbox.connection_pool import SandboxConnectionPool
    from sandbox.executor import SandboxExecutor
    from observability import QUERY_LATENCY, QUERY_REQUESTS, configure_logging


configure_logging()
logger = structlog.get_logger(__name__)


MAX_QUERY_LENGTH = 2000
UNSAFE_QUERY_PATTERN = re.compile(
    r"\b(?:DROP\s+(?:TABLE|DATABASE|INDEX|VIEW)|DELETE\s+FROM|TRUNCATE\s+TABLE|"
    r"ALTER\s+TABLE|INSERT\s+INTO|UPDATE\s+\w+\s+SET|CREATE\s+(?:TABLE|INDEX|VIEW|DATABASE))\b",
    re.IGNORECASE,
)


def validate_user_query(value: str) -> str:
    """Normalize and validate natural-language input at the system boundary."""

    query = value.strip()
    if not query:
        raise ValueError("query must not be empty")
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"query must not exceed {MAX_QUERY_LENGTH} characters")
    if UNSAFE_QUERY_PATTERN.search(query):
        raise ValueError("query contains a forbidden write or DDL instruction")
    return query


class Text2SQLSystem:
    """Production Text2SQL system wiring."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = self._resolve_config_path(config_path)
        self.config_dir = self.config_path.parent
        with self.config_path.open("r", encoding="utf-8") as f:
            self.config = self._expand_env(yaml.safe_load(f))

        self._validate_strict_runtime_config()

        self._init_redis()
        self._init_llm()
        self._init_database_runtimes()
        self._init_retrieval()
        self._init_cache()
        self._init_selector()
        self._init_workflow()

        logger.info("Text2SQL system initialized")

    @staticmethod
    def _resolve_config_path(config_path: str) -> Path:
        path = Path(config_path)
        if path.is_absolute():
            return path
        cwd_path = Path.cwd() / path
        if cwd_path.exists():
            return cwd_path
        package_path = Path(__file__).resolve().parent / path
        return package_path

    def _resolve_data_path(self, path_value: str) -> str:
        path = Path(path_value)
        if path.is_absolute():
            return str(path)
        config_relative = self.config_dir / path
        if config_relative.exists():
            return str(config_relative)
        return str(Path(__file__).resolve().parent / path)

    def _resolve_database_url(self, url: str) -> str:
        if not url.startswith("sqlite:///"):
            return url

        path_value = url.removeprefix("sqlite:///")
        if path_value == ":memory:":
            return url
        if "?" in path_value:
            raise ValueError("SQLite target URL must be a plain file path")

        path = Path(path_value)
        if not path.is_absolute():
            config_relative = self.config_dir / path
            path = (
                config_relative
                if config_relative.exists()
                else Path(__file__).resolve().parent / path
            )
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"SQLite target database does not exist: {path}")
        return f"sqlite:///file:{path.as_posix()}?mode=ro&uri=true"

    @classmethod
    def _expand_env(cls, value):
        if isinstance(value, dict):
            return {key: cls._expand_env(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._expand_env(item) for item in value]
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            return os.environ.get(value[2:-1], "")
        return value

    def _validate_strict_runtime_config(self):
        redis_url = self.config.get("database", {}).get("cache", {}).get("redis_url", "")
        if not redis_url or redis_url.startswith("memory://"):
            raise ValueError("Strict runtime requires an external Redis URL")

        embedding = self.config.get("embedding", {})
        if "bge-m3" not in str(embedding.get("model", "")).lower():
            raise ValueError("Strict runtime requires the BGE-M3 embedding model")

        if not self.config.get("elasticsearch"):
            raise ValueError("Strict runtime requires Elasticsearch configuration")

        agent_config = self.config.get("agent", {})
        retrieval_config = self.config.get("retrieval", {})
        if not retrieval_config.get("business_kb_enabled", False):
            raise ValueError("Strict runtime requires the business knowledge base")
        if not agent_config.get("semantic_cache_enabled", False):
            raise ValueError("Strict runtime requires semantic caching")
        coder_config = self.config.get("llm", {}).get("coder", {})
        if coder_config.get("max_parallel", 1) < agent_config.get("max_candidates", 3):
            raise ValueError("Coder max_parallel must cover all initial SQL candidates")

    def _database_config(self, section: str) -> dict:
        db_config = dict(self.config["database"][section])
        db_config["url"] = self._expand_env(db_config.get("url", ""))
        if not db_config["url"]:
            raise ValueError(
                f"database.{section}.url is not configured; set TEXT2SQL_DB_URL or edit config.yaml"
            )
        db_config["url"] = self._resolve_database_url(db_config["url"])
        return db_config

    def _database_targets_config(self) -> dict:
        database_config = self.config["database"]
        configured_targets = database_config.get("targets")
        if configured_targets is not None:
            if not isinstance(configured_targets, dict) or not configured_targets:
                raise ValueError("database.targets must contain at least one target")

            targets = {}
            for target_db, raw_config in configured_targets.items():
                target_config = dict(raw_config)
                target_config["url"] = self._expand_env(target_config.get("url", ""))
                target_config["metadata_url"] = self._expand_env(
                    target_config.get("metadata_url", target_config["url"])
                )
                if not target_config["url"] or not target_config["metadata_url"]:
                    raise ValueError(f"database.targets.{target_db} requires url and metadata_url")
                target_config["url"] = self._resolve_database_url(target_config["url"])
                target_config["metadata_url"] = self._resolve_database_url(
                    target_config["metadata_url"]
                )
                targets[target_db] = target_config
            return targets

        sandbox_config = self._database_config("sandbox")
        metadata_config = self._database_config("metadata")
        target_db = self.config.get("router", {}).get("default_target_db") or "default"
        sandbox_config["metadata_url"] = metadata_config["url"]
        return {target_db: sandbox_config}

    def _init_redis(self):
        redis_url = self.config["database"]["cache"]["redis_url"]
        self.redis_client = redis.from_url(redis_url)
        self.redis_client.ping()

    def _load_vllm(self):
        try:
            from vllm import LLM, SamplingParams
        except ImportError as exc:
            raise RuntimeError("vLLM is required for non-mock Text2SQLSystem startup") from exc
        return LLM, SamplingParams

    def _init_llm(self):
        planner_config = self.config["llm"]["planner"]
        coder_config = self.config["llm"]["coder"]
        self.planner_llm, self.planner_sampling = self._create_llm(
            planner_config,
            default_temperature=0.1,
            default_stop=["</s>"],
        )
        self.coder_llm, self.sampling_base = self._create_llm(
            coder_config,
            default_temperature=0.7,
            default_stop=["</s>", "```"],
        )
        _, self.sampling_retry = self._create_llm(
            coder_config,
            default_temperature=0.2,
            default_stop=["</s>", "```"],
            temperature_key="retry_temperature",
        )

    def _create_llm(
        self,
        llm_config: dict,
        default_temperature: float,
        default_stop: list,
        temperature_key: str = "temperature",
    ):
        provider = llm_config.get("provider", "vllm")
        if provider == "ollama":
            llm = OllamaLLM(
                model=llm_config["model"],
                base_url=llm_config.get("base_url", "http://127.0.0.1:11434"),
                timeout=llm_config.get("timeout", 180),
                keep_alive=llm_config.get("keep_alive", "10m"),
                max_parallel=llm_config.get("max_parallel", 1),
            )
            sampling = OllamaSamplingParams(
                temperature=llm_config.get(temperature_key, default_temperature),
                top_p=llm_config.get("top_p", 0.9),
                max_tokens=llm_config.get("max_tokens", 1024),
                stop=llm_config.get("stop", default_stop),
                think=llm_config.get("think", False),
            )
            return llm, sampling

        LLM, SamplingParams = self._load_vllm()
        llm = LLM(
            model=llm_config["model"],
            tensor_parallel_size=llm_config.get("tensor_parallel", 1),
            gpu_memory_utilization=llm_config.get("gpu_memory_utilization", 0.9),
            max_model_len=llm_config.get("max_tokens", 2048),
        )
        sampling = SamplingParams(
            temperature=llm_config.get(temperature_key, default_temperature),
            top_p=llm_config.get("top_p", 0.9),
            max_tokens=llm_config.get("max_tokens", 1024),
            stop=llm_config.get("stop", default_stop),
        )
        return llm, sampling

    def _init_database_runtimes(self):
        self.database_runtimes = {}
        redis_url = self.config["database"]["cache"]["redis_url"]
        cost_threshold = self.config["agent"].get("cost_threshold_rows", 10_000_000)

        for target_db, target_config in self._database_targets_config().items():
            pool = SandboxConnectionPool(
                db_url=target_config["url"],
                redis_url=redis_url,
                pool_size=target_config.get("pool_size", 10),
                max_overflow=target_config.get("max_overflow", 20),
                pool_timeout=target_config.get("pool_timeout", 30),
                query_timeout=target_config.get("query_timeout", 5),
            )
            collector = SchemaCollector(
                {
                    "url": target_config["metadata_url"],
                    "cache_namespace": target_db,
                    "schema_version": target_config.get("schema_version"),
                },
                self.redis_client,
            )
            self.database_runtimes[target_db] = {
                "pool": pool,
                "dialect": pool.engine.dialect.name,
                "executor": SandboxExecutor(pool, cost_threshold),
                "schema_collector": collector,
            }

        self.default_target_db = (
            self.config.get("router", {}).get("default_target_db")
            or next(iter(self.database_runtimes))
        )
        if self.default_target_db not in self.database_runtimes:
            raise ValueError(f"router.default_target_db is not configured in database.targets: {self.default_target_db}")

        default_runtime = self.database_runtimes[self.default_target_db]
        self.sandbox_pool = default_runtime["pool"]
        self.executor = default_runtime["executor"]
        self.schema_collector = default_runtime["schema_collector"]

    def _init_retrieval(self):
        retrieval_config = self.config.get("retrieval", {})
        embedding_model = create_embedding_model(self.config["embedding"])
        kb_path = self._resolve_data_path(self.config["paths"]["business_knowledge"])
        self.business_kb = BusinessKnowledgeBase(
            self.redis_client,
            kb_path,
            embedding_model=embedding_model,
            min_score=retrieval_config.get("business_kb_min_score", 0.2),
        )
        self.business_kb.build_index()

        for target_db, runtime in self.database_runtimes.items():
            schema_retriever = SchemaRetriever(
                self.redis_client,
                embedding_model=self.business_kb.embedding_model,
                table_min_score=retrieval_config.get("table_min_score", 0.0),
                column_min_score=retrieval_config.get("column_min_score", 0.0),
                query_aliases=retrieval_config.get("query_aliases"),
                namespace=target_db,
            )
            schema_retriever.build_index(runtime["schema_collector"].inspector)
            runtime["schema_retriever"] = schema_retriever

        self.schema_retriever = self.database_runtimes[self.default_target_db]["schema_retriever"]

        from elasticsearch import Elasticsearch

        es_config = self.config["elasticsearch"]
        es_client = Elasticsearch(es_config["hosts"], request_timeout=30)
        if not es_client.ping():
            raise ConnectionError(f"Elasticsearch is unavailable at {es_config['hosts']}")
        self.entity_linker = EntityLinker(
            es_client,
            index_name=es_config.get("entity_index", "text2sql_entity_index"),
            analyzer=es_config.get("analyzer", "ik_max_word"),
        )

        entity_mappings = self._load_entity_mappings()
        if entity_mappings:
            self.entity_linker.build_index(entity_mappings)

        router_config = self.config.get("router", {})
        router_index_path = self._resolve_data_path(router_config.get("router_index_path", "db_router_index"))
        if os.path.exists(router_index_path):
            vector_db = SemanticRouter.load_db_index(router_index_path)
            self.router = SemanticRouter(vector_db, self.redis_client)
        else:
            descriptor_path = router_config.get("db_descriptors")
            if descriptor_path:
                resolved_descriptor_path = self._resolve_data_path(descriptor_path)
                with open(resolved_descriptor_path, encoding="utf-8") as f:
                    descriptors = json.load(f)
                if not isinstance(descriptors, list) or not descriptors:
                    raise ValueError("router.db_descriptors must contain a non-empty JSON list")
                self.router = SemanticRouter(
                    None,
                    self.redis_client,
                    descriptors=descriptors,
                    embedding_model=embedding_model,
                )
                logger.info("descriptor_router_ready", descriptor_path=resolved_descriptor_path)
            else:
                raise FileNotFoundError(
                    f"Router index is missing and router.db_descriptors is not configured: {router_index_path}"
                )

    def _init_cache(self):
        cache_config = self.config.get("retrieval", {})
        enabled = self.config.get("agent", {}).get("semantic_cache_enabled", True)
        for target_db, runtime in self.database_runtimes.items():
            runtime["semantic_cache"] = SemanticCache(
                self.redis_client,
                embedding_model=self.business_kb.embedding_model,
                threshold=cache_config.get("similarity_threshold", 0.95),
                ttl=self.config["database"]["cache"].get("ttl"),
                namespace=target_db,
                enabled=enabled,
            )
        self.semantic_cache = self.database_runtimes[self.default_target_db]["semantic_cache"]

    def _runtime_for_target(self, target_db: str = "") -> dict:
        if not hasattr(self, "database_runtimes"):
            runtime = {"executor": self.executor}
            for key, attribute in (
                ("pool", "sandbox_pool"),
                ("schema_collector", "schema_collector"),
                ("schema_retriever", "schema_retriever"),
                ("semantic_cache", "semantic_cache"),
            ):
                if hasattr(self, attribute):
                    runtime[key] = getattr(self, attribute)
            return runtime

        resolved_target = target_db or self.default_target_db
        if resolved_target not in self.database_runtimes:
            raise ValueError(f"No database runtime configured for target_db={resolved_target}")
        return self.database_runtimes[resolved_target]

    def _init_selector(self):
        judge_config = self.config["llm"].get("judge")
        judge_llm = None
        if judge_config:
            provider = judge_config.get("provider", "vllm")
            try:
                if provider == "openai":
                    from langchain_openai import ChatOpenAI

                    judge_llm = ChatOpenAI(
                        model=judge_config["model"],
                        api_key=self._expand_env(judge_config.get("api_key", "")),
                        base_url=judge_config.get("base_url"),
                        temperature=judge_config.get("temperature", 0.1),
                        max_tokens=judge_config.get("max_tokens", 512),
                    )
                else:
                    judge_llm, _ = self._create_llm(
                        judge_config,
                        default_temperature=judge_config.get("temperature", 0.1),
                        default_stop=["</s>"],
                    )
            except Exception as exc:
                logger.warning("Judge LLM init failed: %s", exc)
        self.selector = ConsistencySelector(judge_llm=judge_llm)

    def _init_workflow(self):
        agent_config = self.config.get("agent", {})
        retrieval_config = self.config.get("retrieval", {})

        def router_node(state):
            if self.router:
                route_info = self.router.route(state["query"])
                routed_state = {
                    "target_db": route_info["target_db"],
                    "dialect": route_info["dialect"],
                    "dialect_rules": route_info["dialect_rules"],
                }
            else:
                router_config = self.config.get("router", {})
                routed_state = {
                    "target_db": router_config.get("default_target_db", self.default_target_db),
                    "dialect": router_config.get("default_dialect", "mysql"),
                    "dialect_rules": router_config.get("default_dialect_rules", []),
                }
            self._runtime_for_target(routed_state["target_db"])
            return routed_state

        def planner_fn(state):
            runtime = self._runtime_for_target(state.get("target_db", ""))
            return planner_node_with_fallback(
                state,
                llm=self.planner_llm,
                schema_collector=runtime["schema_collector"],
                schema_retriever=runtime["schema_retriever"],
                business_kb=self.business_kb,
                entity_linker=self.entity_linker,
                semantic_cache=runtime["semantic_cache"],
                sampling_params=self.planner_sampling,
                table_top_k=retrieval_config.get("table_top_k", 10),
                column_top_k=retrieval_config.get("column_top_k", 20),
                business_kb_top_k=retrieval_config.get("business_kb_top_k", 3),
                bloodline_max_hops=retrieval_config.get("bloodline_max_hops", 2),
                bloodline_max_tables=retrieval_config.get("bloodline_max_tables"),
                fallback_enabled=agent_config.get("fallback_enabled", True),
            )
        coder_fn = partial(
            coder_node,
            coder_agent=CoderAgentWrapper(self.coder_llm, self.sampling_base, self.sampling_retry),
            max_candidates=agent_config.get("max_candidates", 3),
        )
        def executor_fn(state):
            runtime = self._runtime_for_target(state.get("target_db", ""))
            return executor_node(
                state,
                executor=runtime["executor"],
                selector=self.selector,
                semantic_cache=runtime["semantic_cache"],
                schema_version=runtime["schema_collector"].schema_version,
            )

        init_workflow(router_node, planner_fn, coder_fn, executor_fn)
        self.workflow = create_workflow(max_retries=agent_config.get("max_retries", 3))

    def _load_entity_mappings(self) -> list:
        """Load value-mapping JSON files for the EntityLinker."""

        kb_root = self._resolve_data_path(self.config.get("paths", {}).get("business_knowledge", "./business_knowledge"))
        mapping_dir = Path(kb_root) / "mappings"
        if not mapping_dir.exists():
            return []

        mappings = []
        for path in sorted(mapping_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("dimension") and isinstance(data.get("values"), list):
                mappings.append(data)
        return mappings

    def query(self, user_query: str) -> dict:
        user_query = validate_user_query(user_query)
        trace_id = uuid4().hex
        started = time.perf_counter()
        bind_contextvars(trace_id=trace_id)
        try:
            initial_state = build_initial_state(user_query, trace_id=trace_id)
            result = self.workflow.invoke(initial_state)
            final_sql = result.get("final_sql", "")
            target_db = result.get("target_db", "") or getattr(self, "default_target_db", "")
            dialect = result.get("dialect", "") or self.config.get("router", {}).get(
                "default_dialect", "mysql"
            )
            result_payload = self._execute_result_rows(
                final_sql,
                dialect,
                target_db,
            )
            error_history = list(result.get("error_history", []))
            debug_trace = list(result.get("debug_trace", []))
            debug_trace = append_trace(
                debug_trace,
                "result_fetch",
                "最终结果拉取",
                input={
                    "sql": final_sql,
                    "dialect": dialect,
                    "target_db": target_db,
                },
                output=result_payload,
            )
            if final_sql and result_payload["execution_error"]:
                error_history.append(
                    {
                        "retry": result.get("retry_count", 0),
                        "errors": [
                            {
                                "sql": final_sql,
                                "error": result_payload["execution_error"],
                                "stage": "result_fetch",
                            }
                        ],
                    }
                )
            payload = {
                "sql": final_sql,
                "success": bool(final_sql) and not result_payload["execution_error"],
                "cached": result.get("cached", False),
                "fallback": result.get("fallback", False),
                "target_db": target_db,
                "dialect": dialect,
                "error_history": error_history,
                "trace_id": trace_id,
                "retry_count": result.get("retry_count", 0),
                "debug_trace": debug_trace,
                **result_payload,
            }
            latency = time.perf_counter() - started
            status = "success" if payload["success"] else "failed"
            QUERY_REQUESTS.labels(
                status=status,
                cached=str(payload["cached"]).lower(),
                fallback=str(payload["fallback"]).lower(),
            ).inc()
            QUERY_LATENCY.observe(latency)
            logger.info(
                "text2sql_request",
                query=user_query,
                status=status,
                latency_ms=round(latency * 1000, 2),
                planner_model=self.config["llm"]["planner"]["model"],
                coder_model=self.config["llm"]["coder"]["model"],
                cached=payload["cached"],
                fallback=payload["fallback"],
                retry_count=payload["retry_count"],
            )
            return payload
        except Exception:
            latency = time.perf_counter() - started
            QUERY_REQUESTS.labels(status="error", cached="false", fallback="false").inc()
            QUERY_LATENCY.observe(latency)
            logger.exception(
                "text2sql_request_failed",
                query=user_query,
                latency_ms=round(latency * 1000, 2),
            )
            raise
        finally:
            clear_contextvars()

    def _execute_result_rows(self, sql: str, dialect: str = "", target_db: str = "") -> dict:
        """Execute the final SQL again to return rows to the caller."""

        if not sql:
            return {"data": [], "row_count": 0, "execution_error": ""}

        agent_config = self.config.get("agent", {})
        limit = agent_config.get("result_limit", 100)
        dialect = dialect or self.config.get("router", {}).get("default_dialect", "mysql")
        executor = self._runtime_for_target(target_db)["executor"]
        result = executor.execute(sql, dialect=dialect, limit=limit)
        if result.get("success"):
            return {
                "data": result.get("data", []),
                "row_count": result.get("row_count", 0),
                "execution_error": "",
            }
        return {
            "data": [],
            "row_count": 0,
            "execution_error": result.get("error", "execution failed"),
        }

    def refresh_metadata_indexes(self):
        """Refresh collected schemas and rebuild every retrieval index."""

        for target_db, runtime in self.database_runtimes.items():
            runtime["schema_collector"].collect_and_compress()
            runtime["schema_retriever"].build_index(runtime["schema_collector"].inspector)
            logger.info(
                "schema_indexes_refreshed",
                target_db=target_db,
                schema_version=runtime["schema_collector"].schema_version,
            )

    def start_metadata_scheduler(self):
        if self.config.get("runtime", {}).get("start_metadata_scheduler", True):
            start_scheduler(self.refresh_metadata_indexes)

    def stop(self):
        stop_scheduler()
        if hasattr(self, "database_runtimes"):
            for runtime in self.database_runtimes.values():
                runtime["pool"].engine.dispose()
        logger.info("Text2SQL system stopped")


class CoderAgentWrapper:
    """Adapter around vLLM batch generation used by coder_node."""

    def __init__(self, llm, sampling_base, sampling_retry):
        self.llm = llm
        self.sampling_base = sampling_base
        self.sampling_retry = sampling_retry

    def generate_with_retry(self, prompt: str, n: int = 3) -> list:
        outputs = self.llm.generate([prompt] * n, self.sampling_base)
        return [output.outputs[0].text for output in outputs if output.outputs]

    def single_repair(self, prompt: str) -> str:
        outputs = self.llm.generate([prompt], self.sampling_retry)
        if outputs and outputs[0].outputs:
            return outputs[0].outputs[0].text
        return ""


from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool

@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup()
    try:
        yield
    finally:
        await shutdown()


app_api = FastAPI(title="Text2SQL API", lifespan=lifespan)
text2sql_system = None
FRONTEND_PATH = Path(__file__).resolve().parent / "static" / "index.html"


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=MAX_QUERY_LENGTH)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        return validate_user_query(value)


class QueryResponse(BaseModel):
    sql: str
    success: bool
    cached: bool
    fallback: bool
    target_db: str = ""
    dialect: str = ""
    error_history: list
    data: list = []
    row_count: int = 0
    execution_error: str = ""
    trace_id: str = ""
    retry_count: int = 0
    debug_trace: list = []


async def startup():
    global text2sql_system
    config_path = os.environ.get("TEXT2SQL_CONFIG", "config.yaml")
    text2sql_system = Text2SQLSystem(config_path)
    text2sql_system.start_metadata_scheduler()


async def shutdown():
    if text2sql_system:
        text2sql_system.stop()


@app_api.post("/query", response_model=QueryResponse)
async def query_text2sql(request: QueryRequest):
    if not text2sql_system:
        raise HTTPException(status_code=500, detail="System not initialized")
    result = await run_in_threadpool(text2sql_system.query, request.query)
    return QueryResponse(**result)


@app_api.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(FRONTEND_PATH.read_text(encoding="utf-8"))


@app_api.get("/health")
async def health_check():
    return {"status": "ok", "initialized": text2sql_system is not None}


@app_api.get("/ready")
async def readiness_check():
    if not text2sql_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    if hasattr(text2sql_system, "database_runtimes"):
        database_targets = []
        unavailable = []
        for target_db, runtime in text2sql_system.database_runtimes.items():
            running = runtime["pool"].validate_connection()
            database_targets.append(
                {
                    "target_db": target_db,
                    "dialect": runtime["dialect"],
                    "status": "running" if running else "unavailable",
                }
            )
            if not running:
                unavailable.append(target_db)
    else:
        running = text2sql_system.sandbox_pool.validate_connection()
        database_targets = [
            {
                "target_db": "default",
                "dialect": text2sql_system.config.get("router", {}).get(
                    "default_dialect", "unknown"
                ),
                "status": "running" if running else "unavailable",
            }
        ]
        unavailable = [] if running else ["default"]
    dependency_errors = []
    try:
        if not text2sql_system.redis_client.ping():
            dependency_errors.append("redis")
    except Exception:
        dependency_errors.append("redis")
    try:
        if not text2sql_system.entity_linker.ping():
            dependency_errors.append("elasticsearch")
    except Exception:
        dependency_errors.append("elasticsearch")
    ollama_requirements = {}
    config = getattr(text2sql_system, "config", {})
    for llm_config in config.get("llm", {}).values():
        if isinstance(llm_config, dict) and llm_config.get("provider", "vllm") == "ollama":
            base_url = llm_config.get("base_url", "http://127.0.0.1:11434").rstrip("/")
            ollama_requirements.setdefault(base_url, set()).add(llm_config["model"])
    embedding_config = config.get("embedding", {})
    if embedding_config.get("provider", "ollama") == "ollama" and embedding_config.get("model"):
        base_url = embedding_config.get("base_url", "http://127.0.0.1:11434").rstrip("/")
        ollama_requirements.setdefault(base_url, set()).add(embedding_config["model"])
    for base_url, required_models in ollama_requirements.items():
        try:
            available_models = list_ollama_models(base_url)
        except RuntimeError:
            dependency_errors.append(f"ollama@{base_url}")
            continue
        for model in sorted(required_models - available_models):
            dependency_errors.append(f"ollama-model:{model}")
    unavailable.extend(dependency_errors)
    if unavailable:
        raise HTTPException(
            status_code=503,
            detail=f"Required dependencies are unavailable: {', '.join(unavailable)}",
        )
    return {
        "status": "ready",
        "databases": len(database_targets),
        "database_targets": database_targets,
    }


@app_api.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Text2SQL System")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--query", help="Query to execute")
    args = parser.parse_args()

    system = Text2SQLSystem(args.config)
    system.start_metadata_scheduler()

    if args.query:
        output = system.query(args.query)
        print(f"\nQuery: {args.query}")
        print(f"SQL: {output['sql']}")
        print(f"Success: {output['success']}")
        print(f"Cached: {output['cached']}")
        print(f"Fallback: {output['fallback']}")
        print(f"Trace ID: {output['trace_id']}")
        print(f"Row Count: {output.get('row_count', 0)}")
        if output.get("execution_error"):
            print(f"Execution Error: {output['execution_error']}")
        elif output.get("data"):
            print("Rows:")
            for row in output["data"]:
                print(row)
        if output["error_history"]:
            print(f"Errors: {output['error_history']}")
    else:
        print("Text2SQL system started. Use --query to execute queries.")
