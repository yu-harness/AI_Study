"""Bounded HTTP load test for a running Text2SQL API."""

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


DEFAULT_QUERY = "查询前5个用户"


def run_stress(
    base_url: str,
    request_count: int,
    concurrency: int,
    queries: list,
    timeout: int,
    warmup: bool = False,
) -> dict:
    """Run a finite query workload and return latency/error statistics."""

    endpoint = f"{base_url.rstrip('/')}/query"
    if warmup:
        for query in queries:
            result = _send_query(endpoint, query, timeout)
            if not result["success"]:
                raise RuntimeError(f"Warmup failed: {result['error']}")

    started = time.perf_counter()
    workload = [queries[index % len(queries)] for index in range(request_count)]
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda query: _send_query(endpoint, query, timeout), workload))
    elapsed = time.perf_counter() - started
    return _summarize(results, elapsed, concurrency)


def _send_query(endpoint: str, query: str, timeout: int) -> dict:
    started = time.perf_counter()
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"query": query}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            status = response.status
        error = payload.get("execution_error", "")
        success = status == 200 and bool(payload.get("success"))
        return {
            "success": success,
            "status": status,
            "latency_ms": (time.perf_counter() - started) * 1000,
            "cached": bool(payload.get("cached")),
            "error": error if not success else "",
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "success": False,
            "status": getattr(exc, "code", 0),
            "latency_ms": (time.perf_counter() - started) * 1000,
            "cached": False,
            "error": str(exc),
        }


def _summarize(results: list, elapsed: float, concurrency: int) -> dict:
    latencies = sorted(result["latency_ms"] for result in results)
    successes = sum(1 for result in results if result["success"])
    errors = [result["error"] for result in results if result["error"]]
    return {
        "requests": len(results),
        "concurrency": concurrency,
        "successes": successes,
        "failures": len(results) - successes,
        "cached_responses": sum(1 for result in results if result["cached"]),
        "elapsed_seconds": round(elapsed, 3),
        "throughput_rps": round(len(results) / elapsed, 3) if elapsed else 0.0,
        "latency_ms": {
            "average": round(sum(latencies) / len(latencies), 2),
            "p50": round(_percentile(latencies, 0.50), 2),
            "p95": round(_percentile(latencies, 0.95), 2),
            "max": round(latencies[-1], 2),
        },
        "errors": errors[:10],
    }


def _percentile(sorted_values: list, percentile: float) -> float:
    index = max(0, math.ceil(percentile * len(sorted_values)) - 1)
    return sorted_values[index]


def main():
    parser = argparse.ArgumentParser(description="Run a bounded Text2SQL API pressure test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8011")
    parser.add_argument("--requests", type=int, default=12)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--query", action="append", dest="queries")
    parser.add_argument("--warmup", action="store_true")
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1 or args.timeout < 1:
        parser.error("requests, concurrency, and timeout must be positive")

    summary = run_stress(
        args.base_url,
        request_count=args.requests,
        concurrency=args.concurrency,
        queries=args.queries or [DEFAULT_QUERY],
        timeout=args.timeout,
        warmup=args.warmup,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if summary["failures"] == 0 else 1)


if __name__ == "__main__":
    main()
