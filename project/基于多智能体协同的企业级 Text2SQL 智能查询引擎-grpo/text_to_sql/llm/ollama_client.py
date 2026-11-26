"""
Ollama provider adapter with a small vLLM-compatible response shape.
"""

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import BoundedSemaphore
from typing import List

import structlog

try:
    from ..observability import MODEL_LATENCY, MODEL_TOKENS
except ImportError:  # pragma: no cover - direct module execution
    from observability import MODEL_LATENCY, MODEL_TOKENS


logger = structlog.get_logger(__name__)


def list_ollama_models(base_url: str, timeout: int = 5) -> set[str]:
    """Return model names reported by an Ollama-compatible /api/tags endpoint."""

    endpoint = f"{base_url.rstrip('/')}/api/tags"
    request = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot reach Ollama at {base_url.rstrip('/')}") from exc

    if not isinstance(body, dict):
        raise RuntimeError(f"Invalid Ollama tags response from {base_url.rstrip('/')}")
    models = body.get("models")
    if not isinstance(models, list):
        raise RuntimeError(f"Invalid Ollama tags response from {base_url.rstrip('/')}")
    return {
        name
        for item in models
        if isinstance(item, dict)
        for name in (item.get("name"), item.get("model"))
        if name
    }


@dataclass
class OllamaSamplingParams:
    temperature: float = 0.1
    top_p: float = 0.9
    max_tokens: int = 1024
    stop: List[str] = None
    think: bool | str = False
    format: str | dict | None = None


class _GeneratedText:
    def __init__(self, text: str):
        self.text = text


class _Generation:
    def __init__(self, text: str, metadata: dict = None):
        self.outputs = [_GeneratedText(text)]
        self.metadata = metadata or {}


class OllamaLLM:
    """Minimal Ollama /api/generate client."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:11434",
        timeout: int = 180,
        keep_alive: str = "10m",
        max_parallel: int = 1,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.keep_alive = keep_alive
        self.max_parallel = max(1, int(max_parallel))
        self._parallel_slots = BoundedSemaphore(self.max_parallel)

    def generate(self, prompts: List[str], sampling_params: OllamaSamplingParams = None) -> List[_Generation]:
        params = sampling_params or OllamaSamplingParams()
        if len(prompts) <= 1 or self.max_parallel == 1:
            return [self._coerce_generation(self._generate_one(prompt, params)) for prompt in prompts]

        with ThreadPoolExecutor(max_workers=min(self.max_parallel, len(prompts))) as pool:
            generations = list(pool.map(lambda prompt: self._generate_one(prompt, params), prompts))
        return [self._coerce_generation(generation) for generation in generations]

    def invoke(self, prompt: str) -> str:
        generation = self._coerce_generation(self._generate_one(prompt, OllamaSamplingParams()))
        return generation.outputs[0].text

    def _generate_one(self, prompt: str, params: OllamaSamplingParams) -> _Generation:
        with self._parallel_slots:
            return self._generate_one_unlocked(prompt, params)

    def _generate_one_unlocked(self, prompt: str, params: OllamaSamplingParams) -> _Generation:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": params.think,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": params.temperature,
                "top_p": params.top_p,
                "num_predict": params.max_tokens,
            },
        }
        if params.stop:
            payload["options"]["stop"] = params.stop
        if params.format is not None:
            payload["format"] = params.format

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.base_url}. Start it with `ollama serve`."
            ) from exc

        if "error" in body:
            raise RuntimeError(f"Ollama error for model {self.model}: {body['error']}")
        prompt_tokens = int(body.get("prompt_eval_count", 0) or 0)
        completion_tokens = int(body.get("eval_count", 0) or 0)
        duration_seconds = float(body.get("total_duration", 0) or 0) / 1_000_000_000
        MODEL_TOKENS.labels(model=self.model, direction="prompt").inc(prompt_tokens)
        MODEL_TOKENS.labels(model=self.model, direction="completion").inc(completion_tokens)
        MODEL_LATENCY.labels(model=self.model).observe(duration_seconds)
        logger.info(
            "ollama_generation",
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=round(duration_seconds * 1000, 2),
        )
        return _Generation(
            body.get("response", ""),
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "duration_seconds": duration_seconds,
            },
        )

    @staticmethod
    def _coerce_generation(value) -> _Generation:
        if isinstance(value, _Generation):
            return value
        return _Generation(str(value))
