"""
Multi-granularity schema retrieval with BM25 and dense embeddings.
"""

import json
import re
from typing import List

import jieba
import numpy as np
import redis
from rank_bm25 import BM25Okapi


class SchemaRetriever:
    """Table and column retriever with RRF fusion."""

    DEFAULT_QUERY_ALIASES = {
        "用户": ["user", "users", "customer", "customers"],
        "会员": ["user", "users", "member", "members"],
        "客户": ["user", "users", "customer", "customers"],
        "订单": ["order", "orders"],
        "商品": ["product", "products", "item", "items"],
        "产品": ["product", "products"],
        "金额": ["amount", "price", "revenue", "gmv"],
        "收入": ["revenue", "amount", "gmv"],
        "销售额": ["revenue", "amount", "gmv"],
        "数量": ["count", "num", "qty", "quantity"],
        "姓名": ["name"],
        "名字": ["name"],
        "名称": ["name"],
        "城市": ["city"],
        "地区": ["region", "city"],
        "状态": ["status"],
        "支付": ["paid", "status"],
        "已支付": ["paid", "status"],
        "退款": ["refunded", "status"],
        "创建": ["created_at", "created", "time", "date"],
        "时间": ["time", "date", "created_at"],
        "日期": ["date", "created_at"],
        "活跃": ["active"],
        "user": ["users"],
        "users": ["user", "customer", "customers"],
        "order": ["orders"],
        "orders": ["order"],
        "product": ["products"],
        "products": ["product"],
    }

    def __init__(
        self,
        redis_client: redis.Redis,
        embedding_model=None,
        table_min_score: float = 0.0,
        column_min_score: float = 0.0,
        query_aliases: dict = None,
        namespace: str = "",
    ):
        self.redis = redis_client
        self.prefix = f"schema:retrieve:{namespace}:" if namespace else "schema:retrieve:"
        self.embedding_model = embedding_model or self._load_bge_m3()
        self.bm25_table_index = None
        self.bm25_column_index = None
        self.table_names_cache = []
        self.column_metadata_cache = []
        self.table_min_score = table_min_score
        self.column_min_score = column_min_score
        self.query_aliases = dict(self.DEFAULT_QUERY_ALIASES)
        if query_aliases:
            for key, values in query_aliases.items():
                if isinstance(values, str):
                    self.query_aliases[key] = [values]
                else:
                    self.query_aliases[key] = list(values)

    def _load_bge_m3(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("BAAI/bge-m3")

    def build_index(self, db_inspector):
        """Build table-level and column-level retrieval indexes."""

        tables = db_inspector.get_table_names()
        self.table_names_cache = tables
        if not tables:
            self.bm25_table_index = None
            return

        table_texts = []
        table_metadata = []
        for table in tables:
            comment = self._get_table_comment(db_inspector, table)
            columns = db_inspector.get_columns(table)
            table_texts.append(self._build_table_text(db_inspector, table, comment, columns))
            table_metadata.append({"table": table, "comment": comment})

        self.bm25_table_index = BM25Okapi([self._tokenize(text) for text in table_texts])

        embeddings = self.embedding_model.encode(
            [self._expand_text(text) for text in table_texts],
            normalize_embeddings=True,
        )
        for idx, meta in enumerate(table_metadata):
            self.redis.set(
                f"{self.prefix}table_vec:{meta['table']}",
                json.dumps({"embedding": self._tolist(embeddings[idx]), "metadata": meta}),
            )

        column_texts = []
        self.column_metadata_cache = []
        for table in tables:
            columns = db_inspector.get_columns(table)
            col_texts = []
            col_metadata = []
            for col in columns:
                comment = col.get("comment", "") or ""
                col_text = self._build_column_text(table, col)
                col_texts.append(col_text)
                col_metadata.append(
                    {
                        "table": table,
                        "column": col["name"],
                        "type": str(col["type"]),
                        "comment": comment,
                    }
                )

            if not col_texts:
                continue
            column_texts.extend(col_texts)
            self.column_metadata_cache.extend(col_metadata)
            col_embeddings = self.embedding_model.encode(
                [self._expand_text(text) for text in col_texts],
                normalize_embeddings=True,
            )
            for idx, meta in enumerate(col_metadata):
                self.redis.set(
                    f"{self.prefix}col_vec:{table}:{meta['column']}",
                    json.dumps({"embedding": self._tolist(col_embeddings[idx]), "metadata": meta}),
                )

        self.bm25_column_index = BM25Okapi([self._tokenize(text) for text in column_texts]) if column_texts else None

    def _tokenize(self, text: str) -> List[str]:
        expanded = self._expand_text(text).lower()
        tokens = [token.strip() for token in jieba.cut(expanded) if token.strip()]
        tokens.extend(re.findall(r"[a-z_][a-z0-9_]*|\d+|[\u4e00-\u9fff]", expanded))
        return tokens

    def _build_table_text(self, inspector, table: str, comment: str, columns: list) -> str:
        column_parts = []
        for col in columns:
            column_parts.append(f"{col.get('name', '')} {col.get('type', '')} {col.get('comment', '') or ''}")

        pk = []
        fk_parts = []
        try:
            pk = inspector.get_pk_constraint(table).get("constrained_columns", [])
        except Exception:
            pk = []
        try:
            for fk in inspector.get_foreign_keys(table):
                fk_parts.append(
                    f"{' '.join(fk.get('constrained_columns', []))} {fk.get('referred_table', '')} "
                    f"{' '.join(fk.get('referred_columns', []))}"
                )
        except Exception:
            fk_parts = []

        return " ".join([table, comment or "", " ".join(column_parts), " ".join(pk), " ".join(fk_parts)])

    def _build_column_text(self, table: str, col: dict) -> str:
        return f"{table}.{col['name']} {col['name']} {col.get('type', '')} {col.get('comment', '') or ''}"

    def _expand_text(self, text: str) -> str:
        base = text or ""
        lower = base.lower()
        additions = []
        for key, values in self.query_aliases.items():
            if key.lower() in lower or key in base:
                additions.extend(str(value) for value in values)
        return " ".join([base, *additions])

    def _get_table_comment(self, inspector, table: str) -> str:
        try:
            return inspector.get_table_comment(table).get("text") or ""
        except Exception:
            return ""

    def retrieve_tables(self, query: str, top_k: int = 10) -> List[str]:
        """Return relevant table names ordered by fused sparse/dense score."""

        if not self.table_names_cache:
            return []

        rrf_scores = {}
        k_rrf = 60

        if self.bm25_table_index is not None:
            bm25_scores = self.bm25_table_index.get_scores(self._tokenize(query))
            bm25_ranking = np.argsort(bm25_scores)[::-1][: top_k * 2]
            for rank, idx in enumerate(bm25_ranking):
                if not self._above_min_score(bm25_scores[idx], self.table_min_score):
                    continue
                table = self.table_names_cache[idx]
                rrf_scores[table] = rrf_scores.get(table, 0.0) + 1.0 / (k_rrf + rank + 1)

        query_vec = self.embedding_model.encode(self._expand_text(query), normalize_embeddings=True)
        vec_scores = []
        for table in self.table_names_cache:
            raw = self.redis.get(f"{self.prefix}table_vec:{table}")
            if not raw:
                continue
            cached = json.loads(self._decode(raw))
            table_vec = np.array(cached["embedding"])
            score = float(np.dot(query_vec, table_vec))
            if self._above_min_score(score, self.table_min_score):
                vec_scores.append((table, score))

        vec_scores.sort(key=lambda item: item[1], reverse=True)
        for rank, (table, _) in enumerate(vec_scores[: top_k * 2]):
            rrf_scores[table] = rrf_scores.get(table, 0.0) + 1.0 / (k_rrf + rank + 1)

        for table in self.table_names_cache:
            bonus = self._table_intent_bonus(query, table)
            if bonus:
                rrf_scores[table] = rrf_scores.get(table, 0.0) + bonus

        if not rrf_scores:
            return self.table_names_cache[:top_k]

        return [table for table, _ in sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]]

    def _table_intent_bonus(self, query: str, table: str) -> float:
        """Boost tables whose names or configured aliases are directly requested."""

        query_text = query or ""
        query_lower = query_text.lower()
        table_lower = table.lower()
        table_variants = self._name_variants(table_lower)

        if any(re.search(rf"\b{re.escape(variant)}\b", query_lower) for variant in table_variants):
            return 1.0

        for key, values in self.query_aliases.items():
            key_lower = key.lower()
            if key_lower not in query_lower and key not in query_text:
                continue
            value_variants = set()
            for value in values:
                value_variants.update(self._name_variants(str(value).lower()))
            if table_variants & value_variants:
                return 1.0
        return 0.0

    @staticmethod
    def _name_variants(name: str) -> set:
        variants = {name}
        if name.endswith("s") and len(name) > 1:
            variants.add(name[:-1])
        else:
            variants.add(f"{name}s")
        return variants

    def retrieve_columns(self, query: str, tables: List[str], top_k: int = 20) -> List[str]:
        """Return relevant columns as table.column names."""

        if not tables:
            return []

        query_vec = self.embedding_model.encode(self._expand_text(query), normalize_embeddings=True)
        allowed_tables = set(tables)
        rrf_scores = {}
        metadata_by_name = {}
        k_rrf = 60

        if self.bm25_column_index is not None and self.column_metadata_cache:
            bm25_scores = self.bm25_column_index.get_scores(self._tokenize(query))
            bm25_ranking = np.argsort(bm25_scores)[::-1][: top_k * 4]
            for rank, idx in enumerate(bm25_ranking):
                meta = self.column_metadata_cache[idx]
                if meta["table"] not in allowed_tables:
                    continue
                if not self._above_min_score(bm25_scores[idx], self.column_min_score):
                    continue
                name = f"{meta['table']}.{meta['column']}"
                metadata_by_name[name] = meta
                rrf_scores[name] = rrf_scores.get(name, 0.0) + 1.0 / (k_rrf + rank + 1)

        vec_scores = []
        for table in tables:
            for key in self.redis.scan_iter(f"{self.prefix}col_vec:{table}:*"):
                raw = self.redis.get(key)
                if not raw:
                    continue
                data = json.loads(self._decode(raw))
                col_vec = np.array(data["embedding"])
                score = float(np.dot(query_vec, col_vec))
                if not self._above_min_score(score, self.column_min_score):
                    continue
                meta = data["metadata"]
                vec_scores.append((meta, score))

        vec_scores.sort(key=lambda item: item[1], reverse=True)
        for rank, (meta, _) in enumerate(vec_scores[: top_k * 4]):
            name = f"{meta['table']}.{meta['column']}"
            metadata_by_name[name] = meta
            rrf_scores[name] = rrf_scores.get(name, 0.0) + 1.0 / (k_rrf + rank + 1)

        for name, meta in metadata_by_name.items():
            bonus = self._column_intent_bonus(query, meta)
            if bonus:
                rrf_scores[name] = rrf_scores.get(name, 0.0) + bonus

        if rrf_scores:
            return [name for name, _ in sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]]

        fallback = []
        for meta in self.column_metadata_cache:
            if meta["table"] in allowed_tables:
                fallback.append(f"{meta['table']}.{meta['column']}")
            if len(fallback) >= top_k:
                break
        return fallback

    def _column_intent_bonus(self, query: str, meta: dict) -> float:
        """Boost columns whose names or aliases are directly requested."""

        query_text = query or ""
        query_lower = query_text.lower()
        table = meta.get("table", "")
        column = meta.get("column", "")
        column_variants = self._name_variants(column.lower())
        score = 0.0

        if any(variant and variant in query_lower for variant in column_variants):
            score += 1.2

        for key, values in self.query_aliases.items():
            key_lower = key.lower()
            if key_lower not in query_lower and key not in query_text:
                continue
            value_variants = set()
            for value in values:
                value_variants.update(self._name_variants(str(value).lower()))
            if column_variants & value_variants:
                score += 1.2

        if self._table_intent_bonus(query, table):
            score += 0.3
        return score

    @staticmethod
    def _above_min_score(score, min_score: float) -> bool:
        try:
            return float(score) > float(min_score)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _decode(value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _tolist(value):
        return value.tolist() if hasattr(value, "tolist") else value
