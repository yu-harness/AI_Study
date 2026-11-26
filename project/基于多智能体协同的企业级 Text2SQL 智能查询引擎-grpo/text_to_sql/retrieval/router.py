"""
Semantic router for choosing a target database and dialect rules.
"""

import json
from typing import List

import redis


class SemanticRouter:
    """Route a natural-language query to the most relevant database descriptor."""

    def __init__(
        self,
        vector_db,
        redis_client: redis.Redis,
        descriptors: List[dict] = None,
        embedding_model=None,
    ):
        self.vector_db = vector_db
        self.redis = redis_client
        self.prefix = "router:db:"
        self.descriptors = list(descriptors or [])
        self.embedding_model = embedding_model
        if self.descriptors:
            if self.embedding_model is None:
                raise ValueError("embedding_model is required for descriptor routing")
            texts = [self._descriptor_text(item) for item in self.descriptors]
            vectors = self.embedding_model.encode(texts, normalize_embeddings=True)
            for descriptor, vector in zip(self.descriptors, vectors):
                self.redis.set(
                    f"{self.prefix}descriptor:{descriptor['db_id']}",
                    json.dumps(
                        {
                            "metadata": descriptor,
                            "embedding": vector.tolist() if hasattr(vector, "tolist") else vector,
                        },
                        ensure_ascii=False,
                    ),
                )

    def route(self, query: str) -> dict:
        metadata = self._route_metadata(query)
        if metadata is None:
            return {
                "target_db": "",
                "dialect": "mysql",
                "dialect_rules": [],
                "domain": "",
            }

        return {
            "target_db": metadata.get("db_id", ""),
            "dialect": metadata.get("engine", "mysql"),
            "dialect_rules": metadata.get("special_rules", []),
            "domain": metadata.get("domain", ""),
        }

    def _route_metadata(self, query: str):
        if self.vector_db is not None:
            results = self.vector_db.similarity_search(query, k=1)
            return results[0].metadata if results else None

        descriptor_records = []
        for key in self.redis.scan_iter(f"{self.prefix}descriptor:*"):
            raw = self.redis.get(key)
            if raw:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                descriptor_records.append(json.loads(raw))
        if not descriptor_records:
            return None
        query_vector = self.embedding_model.encode(query, normalize_embeddings=True)
        best = max(
            descriptor_records,
            key=lambda item: self._dot(query_vector, item["embedding"]),
        )
        return best["metadata"]

    @staticmethod
    def _descriptor_text(descriptor: dict) -> str:
        return " ".join(
            [
                descriptor.get("db_id", ""),
                descriptor.get("domain", ""),
                " ".join(descriptor.get("tables", [])),
                " ".join(descriptor.get("keywords", [])),
            ]
        )

    @staticmethod
    def _dot(left, right) -> float:
        return sum(float(a) * float(b) for a, b in zip(left, right))

    @staticmethod
    def build_db_index(descriptors: List[dict], index_path: str = "db_router_index"):
        """Build a FAISS index from database descriptors."""

        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS
        except ImportError as exc:
            raise ImportError("Install langchain-community to build the router index") from exc

        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        texts = [SemanticRouter._descriptor_text(item) for item in descriptors]
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=descriptors)
        vectorstore.save_local(index_path)
        return vectorstore

    @staticmethod
    def load_db_index(index_path: str = "db_router_index"):
        """Load a FAISS database descriptor index."""

        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS
        except ImportError as exc:
            raise ImportError("Install langchain-community to load the router index") from exc

        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
