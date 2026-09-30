import unittest

from vllm_learning_lab.cli import build_parser, format_summary
from vllm_learning_lab.benchmark import BenchmarkSummary


class CLITests(unittest.TestCase):
    def test_parser_accepts_benchmark_arguments(self):
        args = build_parser().parse_args(
            [
                "benchmark",
                "--model",
                "demo",
                "--requests",
                "4",
                "--concurrency",
                "2",
            ]
        )

        self.assertEqual(args.command, "benchmark")
        self.assertEqual(args.model, "demo")
        self.assertEqual(args.requests, 4)
        self.assertEqual(args.concurrency, 2)

    def test_format_summary_is_readable(self):
        summary = BenchmarkSummary(4, 3, 1, 15, 12.5, 8.0, ("RuntimeError: boom",))

        output = format_summary(summary)

        self.assertIn("successes=3", output)
        self.assertIn("failures=1", output)
        self.assertIn("tokens=15", output)
        self.assertIn("RuntimeError: boom", output)


if __name__ == "__main__":
    unittest.main()
