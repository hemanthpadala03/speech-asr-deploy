"""Tiny concurrent load test against a running asrserve instance.

Usage: python scripts/load_test.py --url http://localhost:8000 --n 20 --concurrency 5
Hits /health by default (cheap, no LLM cost); pass --endpoint agent-summarize
to exercise the LLM path instead (costs real tokens).
"""

from __future__ import annotations

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import httpx


def _hit_health(client: httpx.Client, base_url: str) -> float:
    start = time.perf_counter()
    resp = client.get(f"{base_url}/health")
    resp.raise_for_status()
    return time.perf_counter() - start


def _hit_agent_summarize(client: httpx.Client, base_url: str) -> float:
    start = time.perf_counter()
    resp = client.post(
        f"{base_url}/agent/summarize",
        json={"transcript": "The client approved the $1.2M budget for Q3."},
        timeout=30,
    )
    resp.raise_for_status()
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--endpoint", choices=["health", "agent-summarize"], default="health")
    args = parser.parse_args()

    hit = _hit_agent_summarize if args.endpoint == "agent-summarize" else _hit_health

    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            start = time.perf_counter()
            latencies = list(pool.map(lambda _: hit(client, args.url), range(args.n)))
            total = time.perf_counter() - start

    latencies_ms = sorted(l * 1000 for l in latencies)
    print(f"requests={args.n} concurrency={args.concurrency} endpoint={args.endpoint}")
    print(f"total_wall_time_s={total:.2f}  throughput_rps={args.n / total:.2f}")
    print(f"p50_ms={statistics.median(latencies_ms):.1f}  p95_ms={latencies_ms[int(0.95 * len(latencies_ms)) - 1]:.1f}  max_ms={latencies_ms[-1]:.1f}")


if __name__ == "__main__":
    main()
