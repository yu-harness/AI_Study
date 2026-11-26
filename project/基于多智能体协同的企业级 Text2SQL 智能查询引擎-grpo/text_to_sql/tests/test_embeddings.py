import json
import unittest
from unittest.mock import patch

from text_to_sql.retrieval.embeddings import OllamaEmbeddingModel, create_embedding_model


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class TestOllamaEmbeddingModel(unittest.TestCase):
    def test_encode_calls_embed_endpoint_and_normalizes_vectors(self):
        model = OllamaEmbeddingModel(
            model="bge-m3:latest",
            base_url="http://127.0.0.1:8000/",
        )

        with patch(
            "text_to_sql.retrieval.embeddings.urllib.request.urlopen",
            return_value=FakeResponse({"embeddings": [[3.0, 4.0]]}),
        ) as urlopen:
            vector = model.encode("订单金额")

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "http://127.0.0.1:8000/api/embed")
        self.assertEqual(payload, {"model": "bge-m3:latest", "input": ["订单金额"]})
        self.assertEqual(vector, [0.6, 0.8])

    def test_factory_creates_ollama_provider(self):
        model = create_embedding_model(
            {
                "provider": "ollama",
                "model": "bge-m3:latest",
                "base_url": "http://127.0.0.1:8000",
            }
        )

        self.assertIsInstance(model, OllamaEmbeddingModel)


if __name__ == "__main__":
    unittest.main()
