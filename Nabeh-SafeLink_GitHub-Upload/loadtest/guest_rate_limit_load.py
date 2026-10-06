"""Load test for POST /api/v1/scans/guest.

Run only against a staging deployment that you own:
  TARGET_URL=https://staging.example.com \
  CONCURRENCY=20 REQUESTS=200 \
  .venv/bin/python loadtest/guest_rate_limit_load.py
"""

from __future__ import annotations

import asyncio
import os
import statistics
import time
from collections import Counter

import httpx

TARGET_URL = os.getenv("TARGET_URL", "http://127.0.0.1:8000").rstrip("/")
ENDPOINT = f"{TARGET_URL}/api/v1/scans/guest"
CONCURRENCY = max(1, int(os.getenv("CONCURRENCY", "20")))
REQUESTS = max(1, int(os.getenv("REQUESTS", "200")))
TIMEOUT = float(os.getenv("TIMEOUT_SECONDS", "15"))
INPUT_TYPE = os.getenv("INPUT_TYPE", "URL")
INPUT_VALUE = os.getenv("INPUT_VALUE", "https://example.com")


async def send_one(client: httpx.AsyncClient, semaphore: asyncio.Semaphore) -> tuple[int, float, str]:
    async with semaphore:
        started = time.perf_counter()
        try:
            response = await client.post(
                ENDPOINT,
                json={"input_type": INPUT_TYPE, "input_value": INPUT_VALUE, "language": "en"},
            )
            elapsed_ms = (time.perf_counter() - started) * 1000
            return response.status_code, elapsed_ms, response.headers.get("retry-after", "")
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            return 0, elapsed_ms, type(exc).__name__


async def main() -> None:
    print(f"Target: {ENDPOINT}")
    print(f"Requests: {REQUESTS}, concurrency: {CONCURRENCY}")
    print("Use a staging URL. Do not run this against a third-party service.")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    limits = httpx.Limits(
        max_connections=CONCURRENCY,
        max_keepalive_connections=CONCURRENCY,
    )
    timeout = httpx.Timeout(TIMEOUT)

    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        results = await asyncio.gather(
            *(send_one(client, semaphore) for _ in range(REQUESTS))
        )
    elapsed = time.perf_counter() - started

    statuses = Counter(status for status, _, _ in results)
    latencies = sorted(latency for status, latency, _ in results if status != 0)
    retry_after = Counter(value for status, _, value in results if status == 429 and value)

    def percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        index = min(len(values) - 1, round((len(values) - 1) * p))
        return values[index]

    print("\nResults")
    print("-------")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Throughput: {REQUESTS / max(elapsed, 0.001):.2f} requests/s")
    print(f"Statuses: {dict(sorted(statuses.items()))}")
    if latencies:
        print(f"Latency p50: {percentile(latencies, 0.50):.1f} ms")
        print(f"Latency p95: {percentile(latencies, 0.95):.1f} ms")
        print(f"Latency p99: {percentile(latencies, 0.99):.1f} ms")
    print(f"Retry-After values: {dict(retry_after)}")

    allowed = statuses.get(200, 0)
    limited = statuses.get(429, 0)
    errors = REQUESTS - allowed - limited

    # A load test is considered successful when the limiter actively limits
    # excess traffic and does not turn it into a server-error storm.
    if limited == 0:
        raise SystemExit("FAIL: no 429 responses observed; inspect Upstash configuration or limit settings")
    if errors > REQUESTS * 0.05:
        raise SystemExit(f"FAIL: too many transport/5xx errors: {errors}/{REQUESTS}")
    print("PASS: Rate Limiting returned 429 under pressure without excessive errors.")


if __name__ == "__main__":
    asyncio.run(main())
