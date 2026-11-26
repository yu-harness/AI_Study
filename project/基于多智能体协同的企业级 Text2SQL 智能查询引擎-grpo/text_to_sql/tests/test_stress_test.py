import unittest

from text_to_sql.runtime.stress_test import _summarize


class TestStressSummary(unittest.TestCase):
    def test_summary_reports_latency_cache_and_failures(self):
        summary = _summarize(
            [
                {"success": True, "latency_ms": 10.0, "cached": True, "error": ""},
                {"success": True, "latency_ms": 20.0, "cached": False, "error": ""},
                {"success": False, "latency_ms": 30.0, "cached": False, "error": "timeout"},
            ],
            elapsed=0.5,
            concurrency=2,
        )

        self.assertEqual(summary["successes"], 2)
        self.assertEqual(summary["failures"], 1)
        self.assertEqual(summary["cached_responses"], 1)
        self.assertEqual(summary["throughput_rps"], 6.0)
        self.assertEqual(summary["latency_ms"]["p95"], 30.0)
        self.assertEqual(summary["errors"], ["timeout"])


if __name__ == "__main__":
    unittest.main()
