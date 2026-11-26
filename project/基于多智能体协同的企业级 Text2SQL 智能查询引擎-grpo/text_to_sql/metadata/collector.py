"""
Database schema collection and compression.
"""

import hashlib
import json
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional

import redis
from sqlalchemy import MetaData, Table, create_engine, inspect
from sqlalchemy.schema import CreateTable

class SchemaCollector:
    """Collect database metadata and provide compact schema snippets."""

    def __init__(self, db_config: dict, redis_client: redis.Redis):
        self.db_config = db_config
        self.engine = create_engine(db_config["url"])
        self.inspector = inspect(self.engine)
        self.redis = redis_client
        namespace = db_config.get("cache_namespace", "")
        self.prefix = f"schema:compression:{namespace}:" if namespace else "schema:compression:"
        self.max_bloodline_tables = db_config.get("max_bloodline_tables")
        self.schema_version = db_config.get("schema_version") or self._compute_schema_version()

    def refresh_metadata(self):
        """Refresh SQLAlchemy metadata handles and invalidate derived caches."""

        self.inspector = inspect(self.engine)
        self.schema_version = self.db_config.get("schema_version") or self._compute_schema_version()
        if hasattr(self, "_fk_graph_cache"):
            delattr(self, "_fk_graph_cache")

    def collect_all_schemas(self) -> Dict[str, dict]:
        schemas = {}
        for table in self.inspector.get_table_names():
            schemas[table] = self._build_table_schema(table)
        return schemas

    def _build_table_schema(self, table: str) -> dict:
        return {
            "table": table,
            "columns": self._get_columns(table),
            "primary_keys": self._get_primary_keys(table),
            "foreign_keys": self._get_foreign_keys(table),
            "indexes": self.inspector.get_indexes(table),
            "ddl": self._get_ddl(table),
            "comment": self._get_table_comment(table),
        }

    def _get_columns(self, table: str) -> List[dict]:
        columns = []
        for col in self.inspector.get_columns(table):
            columns.append(
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": col.get("default"),
                    "comment": col.get("comment", "") or "",
                }
            )
        return columns

    def _get_primary_keys(self, table: str) -> List[str]:
        pk = self.inspector.get_pk_constraint(table)
        return pk.get("constrained_columns", []) if pk else []

    def _get_foreign_keys(self, table: str) -> List[dict]:
        fks = []
        for fk in self.inspector.get_foreign_keys(table):
            fks.append(
                {
                    "column": fk.get("constrained_columns", []),
                    "referred_table": fk.get("referred_table"),
                    "referred_columns": fk.get("referred_columns", []),
                }
            )
        return fks

    def _get_table_comment(self, table: str) -> str:
        try:
            return self.inspector.get_table_comment(table).get("text") or ""
        except Exception:
            return ""

    def _get_ddl(self, table: str) -> str:
        metadata = MetaData()
        reflected_table = Table(table, metadata, autoload_with=self.engine)
        return str(CreateTable(reflected_table).compile(dialect=self.engine.dialect)).strip()

    def collect_and_compress(self, hot_columns: Optional[Dict[str, List[str]]] = None):
        """Collect all schemas and cache compressed versions."""

        self.refresh_metadata()
        for table, schema in self.collect_all_schemas().items():
            target_cols = hot_columns.get(table, []) if hot_columns else []
            self._cache_schema(table, schema, target_cols)

    def get_compressed_schema(
        self,
        tables: List[str],
        target_columns: Optional[List[str]] = None,
    ) -> str:
        """Return compressed schema text for the requested tables."""

        snippets = []
        for table in tables:
            target_for_table = self._target_columns_for_table(table, target_columns or [])
            key = self._compression_key(table, target_for_table)
            raw = self.redis.get(key)
            cached = json.loads(self._decode(raw)) if raw else None

            if (
                not cached
                or cached.get("schema_version") != self.schema_version
                or set(cached.get("target_columns", [])) != set(target_for_table)
            ):
                schema = self._build_table_schema(table)
                self._cache_schema(table, schema, target_for_table)
                raw = self.redis.get(key)
                cached = json.loads(self._decode(raw)) if raw else None

            snippets.append(cached["compressed"] if cached else f"Table {table}: (not found)")

        return "\n\n".join(snippets)

    def _cache_schema(self, table: str, schema: dict, target_columns: Optional[List[str]] = None):
        compressed = self._compress_ddl(schema.get("ddl", ""), schema, target_columns=target_columns)
        self.redis.set(
            self._compression_key(table, target_columns or []),
            json.dumps(
                {
                    "compressed": compressed,
                    "full_ddl": schema.get("ddl", ""),
                    "target_columns": target_columns or [],
                    "schema_version": getattr(self, "schema_version", "unknown"),
                    "metadata": schema,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
            ),
        )

    def _compression_key(self, table: str, target_columns: List[str]) -> str:
        payload = {
            "schema_version": getattr(self, "schema_version", "unknown"),
            "target_columns": sorted(str(col).lower() for col in target_columns),
        }
        normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()[:12]
        return f"{self.prefix}{table}:{digest}"

    def _compress_ddl(
        self,
        ddl: str,
        schema: dict,
        target_columns: Optional[List[str]] = None,
    ) -> str:
        """Compress table metadata while preserving join and target columns."""

        table = schema.get("table", "unknown")
        target_set = {col.lower() for col in target_columns or []}
        pk_cols = {col.lower() for col in schema.get("primary_keys", [])}
        fk_cols, fk_refs = self._foreign_key_sets(schema)

        selected = []
        for col in schema.get("columns", []):
            name = col["name"]
            lower = name.lower()
            if self._should_keep_column(table, lower, target_set, pk_cols, fk_cols):
                tags = []
                if lower in pk_cols:
                    tags.append("PK")
                if lower in fk_refs:
                    tags.append(fk_refs[lower])
                if not col.get("nullable", True):
                    tags.append("NOT NULL")
                tag_text = f" ({', '.join(tags)})" if tags else ""
                comment = f": {col.get('comment', '')}" if col.get("comment") else ""
                selected.append(f"  - {name} ({col.get('type', '')}){tag_text}{comment}")

        if not selected:
            for col in schema.get("columns", [])[:8]:
                selected.append(f"  - {col['name']} ({col.get('type', '')})")

        header = f"Table {table}"
        if schema.get("comment"):
            header += f" ({schema['comment']})"
        return header + ":\n" + "\n".join(selected)

    def _target_columns_for_table(self, table: str, target_columns: List[str]) -> List[str]:
        table_lower = table.lower()
        selected = []
        for col in target_columns:
            col_lower = col.lower()
            if "." in col_lower:
                source_table, source_col = col_lower.split(".", 1)
                if source_table == table_lower:
                    selected.append(source_col)
            else:
                selected.append(col_lower)
        return selected

    @staticmethod
    def _foreign_key_sets(schema: dict):
        fk_cols = set()
        fk_refs = {}
        for fk in schema.get("foreign_keys", []):
            for src_col, dst_col in zip(fk.get("column", []), fk.get("referred_columns", [])):
                lower = src_col.lower()
                fk_cols.add(lower)
                fk_refs[lower] = f"FK -> {fk.get('referred_table')}.{dst_col}"
        return fk_cols, fk_refs

    @staticmethod
    def _should_keep_column(table: str, column: str, target_set: set, pk_cols: set, fk_cols: set) -> bool:
        full_name = f"{table.lower()}.{column}"
        is_target = column in target_set or full_name in target_set
        is_relationship = column == "id" or column.endswith("_id") or column.endswith("_key")
        return is_target or column in pk_cols or column in fk_cols or is_relationship

    def bloodline_completion(
        self,
        seed_tables: List[str],
        max_hops: int = 2,
        max_tables: Optional[int] = None,
    ) -> List[str]:
        """Expand candidate tables through foreign-key relationships."""

        if not hasattr(self, "_fk_graph_cache"):
            self._fk_graph_cache = self._build_fk_graph()

        limit = max_tables if max_tables is not None else self.max_bloodline_tables
        seeds = []
        queued = set()
        for table in seed_tables:
            if table in self._fk_graph_cache and table not in queued:
                seeds.append(table)
                queued.add(table)

        ordered = []
        visited = set()
        queue = deque((table, 0) for table in seeds)
        while queue:
            table, depth = queue.popleft()
            if table in visited:
                continue
            visited.add(table)
            ordered.append(table)
            if limit and len(ordered) >= limit:
                break
            if depth >= max_hops:
                continue
            for related_table in self._fk_graph_cache.get(table, []):
                if related_table not in visited and related_table not in queued:
                    queue.append((related_table, depth + 1))
                    queued.add(related_table)
        return ordered

    def _build_fk_graph(self) -> Dict[str, List[str]]:
        tables = self.inspector.get_table_names()
        table_order = {table: idx for idx, table in enumerate(tables)}
        graph = {table: [] for table in tables}

        def add_edge(left: str, right: str):
            if left in graph and right in table_order and right not in graph[left]:
                graph[left].append(right)

        for table in tables:
            for fk in self._get_foreign_keys(table):
                referred = fk.get("referred_table")
                if referred:
                    add_edge(table, referred)
                    add_edge(referred, table)
        for table in graph:
            graph[table].sort(key=lambda item: table_order.get(item, len(table_order)))
        return graph

    def _compute_schema_version(self) -> str:
        """Create a stable metadata fingerprint for cache invalidation."""

        payload = []
        for table in sorted(self.inspector.get_table_names()):
            payload.append(
                {
                    "table": table,
                    "columns": [
                        {
                            "name": col.get("name"),
                            "type": str(col.get("type")),
                            "nullable": col.get("nullable", True),
                            "default": col.get("default"),
                        }
                        for col in self.inspector.get_columns(table)
                    ],
                    "primary_keys": self._get_primary_keys(table),
                    "foreign_keys": self._get_foreign_keys(table),
                }
            )
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def get_all_table_names(self) -> List[str]:
        return self.inspector.get_table_names()

    def get_hot_tables(self, top_k: int = 5) -> List[str]:
        return self.inspector.get_table_names()[:top_k]

    @staticmethod
    def _decode(value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)
