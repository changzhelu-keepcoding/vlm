import unittest

from vllm_learning_lab.benchmark import BenchmarkSummary, run_benchmark
from vllm_learning_lab.client import ChatResult, Usage


class FakeClient:
    def __init__(self):
        self.calls = []

    def chat(self, *, model, prompt):
        self.calls.append((model, prompt))
        if prompt == "fail":
            raise RuntimeError("simulated server error")
        return ChatResult(
            content=f"answer: {prompt}",
            model=model,
            usage=Usage(prompt_tokens=2, completion_tokens=3, total_tokens=5),
        )


class BenchmarkTests(unittest.TestCase):
    def test_run_benchmark_collects_successes_failures_and_metrics(self):
        client = FakeClient()

        summary = run_benchmark(
            client,
            model="demo",
            prompts=["one", "two", "fail", "four"],
            concurrency=2,
        )

        self.assertIsInstance(summary, BenchmarkSummary)
        self.assertEqual(summary.total_requests, 4)
        self.assertEqual(summary.successes, 3)
        self.assertEqual(summary.failures, 1)
        self.assertEqual(summary.total_tokens, 15)
        self.assertGreater(summary.average_latency_ms, 0)
        self.assertGreater(summary.requests_per_second, 0)
        self.assertEqual(len(client.calls), 4)

    def test_run_benchmark_rejects_invalid_concurrency(self):
        with self.assertRaises(ValueError):
            run_benchmark(FakeClient(), model="demo", prompts=["one"], concurrency=0)


if __name__ == "__main__":
    unittest.main()
