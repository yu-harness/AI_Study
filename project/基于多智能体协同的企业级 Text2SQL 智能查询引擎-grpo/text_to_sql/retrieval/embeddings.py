"""
Embedding helpers for production and dependency-light local modes.
"""

import json
import math
import urllib.error
import urllib.request


class OllamaEmbeddingModel:
    """Embedding adapter for a local Ollama-compatible ``/api/embed`` endpoint."""

    def __init__(
        self,
        model: str = "bge-m3:latest",
        base_url: str = "http://127.0.0.1:11434",
        timeout: int = 60,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def encode(self, texts, normalize_embeddings: bool = True):
        single_input = isinstance(texts, str)
        inputs = [texts] if single_input else list(texts)
        payload = json.dumps({"model": self.model, "input": inputs}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach Ollama embeddings at {self.base_url}."
            ) from exc

        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(inputs):
            raise RuntimeError(f"Ollama embedding response is invalid for model {self.model}")

        if normalize_embeddings:
            embeddings = [self._normalize(vector) for vector in embeddings]
        return embeddings[0] if single_input else embeddings

    @staticmethod
    def _normalize(vector):
        norm = math.sqrt(sum(float(value) * float(value) for value in vector))
        return [float(value) / norm for value in vector] if norm else [float(value) for value in vector]


def create_embedding_model(config: dict = None):
    """Create an embedding model from config.

    provider=ollama uses a local Ollama-compatible endpoint, while
    provider=sentence-transformers loads a configured SentenceTransformer model.
    """

    config = config or {}
    provider = config.get("provider", "ollama")
    if provider == "ollama":
        return OllamaEmbeddingModel(
            model=config.get("model", "bge-m3:latest"),
            base_url=config.get("base_url", "http://127.0.0.1:11434"),
            timeout=config.get("timeout", 60),
        )

    if provider in ("sentence-transformers", "sentence_transformers"):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(config.get("model", "BAAI/bge-m3"))

    raise ValueError(f"Unsupported embedding provider: {provider}")
