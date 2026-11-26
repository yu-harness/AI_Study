import json
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from unittest.mock import MagicMock, patch

from text_to_sql.llm.ollama_client import OllamaLLM, OllamaSamplingParams, list_ollama_models


class TestOllamaLLM(unittest.TestCase):
    def test_lists_installed_models_from_tags_endpoint(self):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "models": [
                    {"name": "qwen3.5:4b", "model": "qwen3.5:4b"},
                    {"name": "bge-m3:latest", "model": "bge-m3:latest"},
                ]
            }
        ).encode("utf-8")
        response.__enter__.return_value = response

        with patch(
            "text_to_sql.llm.ollama_client.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            models = list_ollama_models("http://127.0.0.1:8000/")

        self.assertEqual(models, {"qwen3.5:4b", "bge-m3:latest"})
        self.assertEqual(urlopen.call_args.args[0].full_url, "http://127.0.0.1:8000/api/tags")

    def test_parallel_generation_preserves_prompt_order(self):
        llm = OllamaLLM(model="qwen3.5:4b", max_parallel=2)

        with patch.object(llm, "_generate_one", side_effect=lambda prompt, params: prompt.upper()):
            outputs = llm.generate(["first", "second"], OllamaSamplingParams())

        self.assertEqual([output.outputs[0].text for output in outputs], ["FIRST", "SECOND"])

    def test_parallel_limit_applies_across_concurrent_callers(self):
        llm = OllamaLLM(model="qwen3.5:4b", max_parallel=1)
        state = {"active": 0, "maximum": 0}
        lock = Lock()

        def generate_one(prompt, params):
            with lock:
                state["active"] += 1
                state["maximum"] = max(state["maximum"], state["active"])
            time.sleep(0.02)
            with lock:
                state["active"] -= 1
            return prompt

        with patch.object(llm, "_generate_one_unlocked", side_effect=generate_one):
            with ThreadPoolExecutor(max_workers=4) as pool:
                outputs = list(pool.map(llm.invoke, ["a", "b", "c", "d"]))

        self.assertEqual(outputs, ["a", "b", "c", "d"])
        self.assertEqual(state["maximum"], 1)

    def test_generation_explicitly_disables_native_thinking(self):
        llm = OllamaLLM(model="qwen3.5:4b")
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"response": "ok", "prompt_eval_count": 1, "eval_count": 1}
        ).encode("utf-8")
        response.__enter__.return_value = response

        with patch(
            "text_to_sql.llm.ollama_client.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            output = llm.generate(["prompt"], OllamaSamplingParams(think=False))[0]

        payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertIs(payload["think"], False)
        self.assertEqual(output.outputs[0].text, "ok")

    def test_generation_forwards_structured_output_schema(self):
        llm = OllamaLLM(model="qwen3.5:4b")
        response = MagicMock()
        response.read.return_value = json.dumps({"response": '{"score": 1}'}).encode("utf-8")
        response.__enter__.return_value = response
        schema = {
            "type": "object",
            "properties": {"score": {"type": "number"}},
            "required": ["score"],
        }

        with patch(
            "text_to_sql.llm.ollama_client.urllib.request.urlopen",
            return_value=response,
        ) as urlopen:
            llm.generate(["prompt"], OllamaSamplingParams(format=schema))

        payload = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(payload["format"], schema)


if __name__ == "__main__":
    unittest.main()
