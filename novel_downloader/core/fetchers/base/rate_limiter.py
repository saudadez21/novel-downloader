#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.base.rate_limiter
------------------------------------------------

"""

import asyncio
import random
import time


class RateLimiter:
    """
    Simple async token-bucket rate limiter:
    ensures no more than rate_per_sec
    requests are started per second, across all coroutines.
    """

    def __init__(self, rate_per_sec: float):
        self._interval = 1.0 / rate_per_sec
        self._lock = asyncio.Lock()
        self._last = time.monotonic()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            delay = self._interval - elapsed
            if delay > 0:
                jitter = random.uniform(0, 0.3)
                await asyncio.sleep(delay + jitter)
            self._last = time.monotonic()


class RateLimiterV2:
    def __init__(self, rate_per_sec: float):
        self._interval = 1.0 / rate_per_sec
        self._lock = asyncio.Lock()
        self._next_allowed_time = time.monotonic()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if now < self._next_allowed_time:
                delay = self._next_allowed_time - now
                jitter = random.uniform(0, 0.05 * self._interval)
                await asyncio.sleep(delay + jitter)
            self._next_allowed_time = max(now, self._next_allowed_time) + self._interval


class TokenBucketRateLimiter:
    def __init__(
        self,
        rate: float,
        burst: int = 10,
        jitter_strength: float = 0.3,
    ):
        self.rate = rate
        self.capacity = burst
        self.tokens = burst
        self.timestamp = time.monotonic()
        self.lock = asyncio.Lock()
        self.jitter_strength = jitter_strength

    async def wait(self) -> None:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.timestamp

            self.tokens = min(self.capacity, int(self.tokens + elapsed * self.rate))
            self.timestamp = now

            if self.tokens >= 1:
                self.tokens -= 1
                jitter = random.uniform(-self.jitter_strength, self.jitter_strength)
                if jitter > 0:
                    await asyncio.sleep(jitter)
                return
            else:
                wait_time = (1 - self.tokens) / self.rate
                jitter = random.uniform(-self.jitter_strength, self.jitter_strength)
                total_wait = max(0.0, wait_time + jitter)
                await asyncio.sleep(total_wait)
                self.timestamp = time.monotonic()
                self.tokens = max(0, self.tokens - 1)
