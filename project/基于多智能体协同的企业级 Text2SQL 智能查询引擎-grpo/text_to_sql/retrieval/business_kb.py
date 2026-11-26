"""
Business knowledge retrieval with dense vectors plus keyword fallback.
"""

import glob
import json
import os
from typing import List

import numpy as np
import redis


class BusinessKnowledgeBase:
    """Load JSON business knowledge files into Redis-backed indexes."""

    def __init__(
        self,
        redis_client: redis.Redis,
        kb_path: str = "./business_knowledge",
        embedding_model=None,
        min_score: float = 0.2,
    ):
        self.redis = redis_client
        self.kb_path = kb_path
        self.prefix = "kb:business:"
        self.vec_prefix = "kb:vec:"
        self.embedding_model = embedding_model or self._load_bge_m3()
        self.min_score = min_score

    def _load_bge_m3(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("BAAI/bge-m3")

    def build_index(self):
        """Load knowledge JSON files and vectorize searchable text."""

        kb_files = glob.glob(os.path.join(self.kb_path, "**/*.json"), recursive=True)
        for filepath in kb_files:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            doc_id = data.get("id", filepath)
            self.redis.set(f"{self.prefix}{doc_id}", json.dumps(data, ensure_ascii=False))

            embed_text = self._build_embedding_text(data)
            if embed_text:
                embedding = self.embedding_model.encode(embed_text, normalize_embeddings=True)
                self.redis.set(f"{self.vec_prefix}{doc_id}", json.dumps(self._tolist(embedding)))

    def search(self, query: str, rewritten_query: str = None, top_k: int = 3) -> str:
        """Return formatted knowledge snippets for a query."""

        search_text = f"{query} {rewritten_query or ''}".strip()
        results = []
        seen = set()

        for doc_id, _, content in self._vector_search(search_text, top_k=top_k):
            if doc_id not in seen:
                seen.add(doc_id)
                results.append(content)

        for doc_id, content in self._keyword_search(search_text):
            if doc_id not in seen:
                seen.add(doc_id)
                results.append(content)

        if not results:
            return "无相关业务知识"
        return "\n".join(f"- {content}" for content in results)

    def _vector_search(self, query: str, top_k: int = 3) -> List[tuple]:
        query_vec = self.embedding_model.encode(query, normalize_embeddings=True)
        candidates = []
        for key in self.redis.scan_iter(f"{self.vec_prefix}*"):
            doc_id = self._decode(key).replace(self.vec_prefix, "")
            raw = self.redis.get(key)
            if not raw:
                continue
            doc_vec = np.array(json.loads(self._decode(raw)))
            candidates.append((doc_id, float(np.dot(query_vec, doc_vec))))

        candidates.sort(key=lambda item: item[1], reverse=True)
        results = []
        for doc_id, score in candidates[:top_k]:
            if score < self.min_score:
                continue
            raw = self.redis.get(f"{self.prefix}{doc_id}")
            if raw:
                results.append((doc_id, score, self._format_content(json.loads(self._decode(raw)))))
        return results

    def _keyword_search(self, query: str) -> List[tuple]:
        results = []
        for key in self.redis.scan_iter(f"{self.prefix}*"):
            doc_id = self._decode(key).replace(self.prefix, "")
            raw = self.redis.get(key)
            if not raw:
                continue
            data = json.loads(self._decode(raw))
            if self._matches_keywords(query, data):
                results.append((doc_id, self._format_content(data)))
        return results

    @staticmethod
    def _build_embedding_text(data: dict) -> str:
        texts = []
        texts.extend(data.get("question_patterns", []))
        texts.extend(data.get("keywords", []))
        if data.get("definition"):
            texts.append(data["definition"])
        for metric in data.get("metrics", []):
            texts.append(metric.get("name", ""))
            texts.extend(metric.get("alias", []))
            texts.append(metric.get("sql_template", ""))
        return " | ".join(text for text in texts if text)

    @staticmethod
    def _matches_keywords(query: str, data: dict) -> bool:
        for keyword in data.get("keywords", []):
            if keyword and keyword in query:
                return True
        for pattern in data.get("question_patterns", []):
            if pattern and pattern in query:
                return True
        for metric in data.get("metrics", []):
            if metric.get("name") and metric["name"] in query:
                return True
            if any(alias and alias in query for alias in metric.get("alias", [])):
                return True
        return False

    @staticmethod
    def _format_content(data: dict) -> str:
        if "metrics" in data:
            parts = []
            if data.get("definition"):
                parts.append(data["definition"])
            for metric in data["metrics"]:
                metric_text = f"{metric.get('name')}: {metric.get('sql_template')}"
                if metric.get("unit"):
                    metric_text = f"{metric_text}, unit={metric.get('unit')}"
                parts.append(metric_text)
            if data.get("filters"):
                parts.append(f"filters={json.dumps(data['filters'], ensure_ascii=False)}")
            return f"【指标】{'; '.join(parts)}"
        if "definition" in data:
            parts = [data["definition"]]
            if data.get("filters"):
                parts.append(f"filters={json.dumps(data['filters'], ensure_ascii=False)}")
            return f"【{data.get('id', 'knowledge')}】{'; '.join(parts)}"
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def _decode(value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _tolist(value):
        return value.tolist() if hasattr(value, "tolist") else value
