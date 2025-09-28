#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.rate_limiter
-------------------------------------------

An asyncio-compatible token bucket rate limiter.
"""

import asyncio
import random
import time


class TokenBucketRateLimiter:
    def __init__(
        self,
        rate: float,
        burst: int = 10,
        jitter_strength: float = 0.3,
    ):
        """
        A simple asyncio-compatible token bucket rate limiter.

        :param rate: Tokens added per second.
        :param burst: Maximum bucket size (burst capacity).
        :param jitter_strength: Jitter range in seconds (+/-).
        """
        self.rate = rate
        self.capacity = burst
        self.tokens = float(burst)
        self.timestamp = time.monotonic()
        self.lock = asyncio.Lock()
        self.jitter_strength = jitter_strength

    async def wait(self) -> None:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.timestamp

            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.timestamp = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return

            wait_time = (1.0 - self.tokens) / self.rate
            jitter = random.uniform(-self.jitter_strength, self.jitter_strength)
            total_wait = max(0.0, wait_time + jitter)

        await asyncio.sleep(total_wait)

        async with self.lock:
            self.timestamp = time.monotonic()
            self.tokens = max(0.0, self.tokens - 1.0)
