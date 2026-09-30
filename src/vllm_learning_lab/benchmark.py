"""Simple concurrency experiments for an OpenAI-compatible model server."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time
from typing import Sequence

from .client import VLLMClient


@dataclass(frozen=True)
class BenchmarkSummary:
    total_requests: int
    successes: int
    failures: int
    total_tokens: int
    average_latency_ms: float
    requests_per_second: float
    errors: tuple[str, ...] = ()


def run_benchmark(
    client: VLLMClient,
    *,
    model: str,
    prompts: Sequence[str],
    concurrency: int = 1,
) -> BenchmarkSummary:
    if concurrency < 1:
        raise ValueError("concurrency must be at least 1")

    started = time.perf_counter()
    latencies: list[float] = []
    total_tokens = 0
    errors: list[str] = []

    def request(prompt: str) -> tuple[float, int, str | None]:
        request_started = time.perf_counter()
        try:
            result = client.chat(model=model, prompt=prompt)
            return time.perf_counter() - request_started, result.usage.total_tokens, None
        except Exception as exc:  # A benchmark should report one bad request and continue.
            return time.perf_counter() - request_started, 0, f"{type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(request, prompt) for prompt in prompts]
        for future in as_completed(futures):
            latency, tokens, error = future.result()
            latencies.append(latency)
            total_tokens += tokens
            if error:
                errors.append(error)

    elapsed = max(time.perf_counter() - started, 1e-12)
    total_requests = len(prompts)
    failures = len(errors)
    successes = total_requests - failures
    average_latency_ms = (sum(latencies) / len(latencies) * 1000) if latencies else 0.0
    requests_per_second = successes / elapsed
    return BenchmarkSummary(
        total_requests=total_requests,
        successes=successes,
        failures=failures,
        total_tokens=total_tokens,
        average_latency_ms=average_latency_ms,
        requests_per_second=requests_per_second,
        errors=tuple(errors),
    )
