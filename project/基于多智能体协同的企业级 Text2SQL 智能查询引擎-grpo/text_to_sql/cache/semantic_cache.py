"""
Semantic cache backed by Redis vectors.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

import numpy as np


class SemanticCache:
    """Small-scale semantic cache using Redis key scans."""

    def __init__(
        self,
        redis_client,
        embedding_model=None,
        threshold: float = 0.95,
        ttl: int = None,
        namespace: str = "",
        enabled: bool = True,
    ):
        self.redis = redis_client
        self.prefix = f"cache:semantic:{namespace}:" if namespace else "cache:semantic:"
        self.threshold = threshold
        self.ttl = ttl
        self.enabled = enabled

        if embedding_model is None:
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer("BAAI/bge-m3")
        else:
            self.embedding_model = embedding_model

    def _embed(self, text: str) -> np.ndarray:
        return np.array(self.embedding_model.encode(text, normalize_embeddings=True))

    def get(self, query: str, schema_version: str = "") -> Optional[str]:
        """Return cached SQL when semantic similarity reaches the threshold."""

        hit = self.get_with_score(query, schema_version=schema_version)
        return hit["sql"] if hit else None

    def get_with_score(self, query: str, schema_version: str = "") -> Optional[dict]:
        """Return cached SQL with score and metadata for diagnostics."""

        if not self.enabled:
            return None
        query_vec = self._embed(query)
        best = {"score": -1.0, "sql": None, "metadata": None}

        for key in self.redis.scan_iter(f"{self.prefix}vec:*"):
            key_text = self._decode(key)
            doc_id = key_text.replace(f"{self.prefix}vec:", "")
            vec_data = self.redis.get(key)
            if not vec_data:
                continue
            cached_vec = np.array(json.loads(self._decode(vec_data)))
            meta_data = self.redis.get(f"{self.prefix}meta:{doc_id}")
            metadata = json.loads(self._decode(meta_data)) if meta_data else {}
            if schema_version and metadata.get("schema_version", "") != schema_version:
                continue
            score = float(np.dot(query_vec, cached_vec))
            if score > best["score"]:
                sql_data = self.redis.get(f"{self.prefix}sql:{doc_id}")
                best = {
                    "score": score,
                    "sql": self._decode(sql_data) if sql_data else None,
                    "metadata": metadata,
                }

        if best["sql"] and best["score"] >= self.threshold:
            return best
        return None

    def set(self, query: str, sql: str, schema_version: str = ""):
        """Write query vector, SQL, and diagnostics metadata."""

        if not self.enabled:
            return
        doc_id = hashlib.md5(query.encode("utf-8")).hexdigest()
        vec = self._embed(query)
        metadata = {
            "query": query,
            "schema_version": schema_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        self._redis_set(f"{self.prefix}vec:{doc_id}", json.dumps(self._tolist(vec)))
        self._redis_set(f"{self.prefix}sql:{doc_id}", sql)
        self._redis_set(f"{self.prefix}meta:{doc_id}", json.dumps(metadata, ensure_ascii=False))

    def _redis_set(self, key: str, value: str):
        if self.ttl:
            try:
                self.redis.set(key, value, ex=self.ttl)
                return
            except TypeError:
                pass
        self.redis.set(key, value)

    @staticmethod
    def _decode(value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _tolist(value):
        return value.tolist() if hasattr(value, "tolist") else value
