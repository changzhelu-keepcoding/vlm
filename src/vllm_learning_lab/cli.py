"""Command-line entry points for the learning lab."""

import argparse

from .benchmark import BenchmarkSummary, run_benchmark
from .client import VLLMClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Small vLLM learning experiments")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--api-key", default="EMPTY")
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke", help="send one chat request")
    smoke.add_argument("--model", required=True)
    smoke.add_argument("--prompt", required=True)
    smoke.add_argument("--system")
    smoke.add_argument("--max-tokens", type=int, default=128)

    benchmark = subparsers.add_parser("benchmark", help="run a concurrency experiment")
    benchmark.add_argument("--model", required=True)
    benchmark.add_argument("--prompt", default="Explain continuous batching in one sentence.")
    benchmark.add_argument("--requests", type=int, default=8)
    benchmark.add_argument("--concurrency", type=int, default=2)
    return parser


def format_summary(summary: BenchmarkSummary) -> str:
    lines = [
        (
            f"requests={summary.total_requests} "
            f"successes={summary.successes} failures={summary.failures}"
        ),
        f"tokens={summary.total_tokens}",
        f"avg_latency_ms={summary.average_latency_ms:.2f}",
        f"requests_per_second={summary.requests_per_second:.2f}",
    ]
    if summary.errors:
        lines.append("errors:")
        lines.extend(f"- {error}" for error in summary.errors)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = VLLMClient(args.base_url, api_key=args.api_key)

    if args.command == "smoke":
        result = client.chat(
            model=args.model,
            prompt=args.prompt,
            system=args.system,
            max_tokens=args.max_tokens,
        )
        print(result.content)
        print(f"usage: {result.usage}")
        return 0

    prompts = [args.prompt] * args.requests
    summary = run_benchmark(
        client,
        model=args.model,
        prompts=prompts,
        concurrency=args.concurrency,
    )
    print(format_summary(summary))
    return 0 if summary.failures == 0 else 1
