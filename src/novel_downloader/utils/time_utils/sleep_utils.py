#!/usr/bin/env python3
"""
novel_downloader.utils.time_utils.sleep_utils
---------------------------------------------

Utilities for adding randomized delays in scripts and bots.

Includes:
- sleep_with_random_delay(): Sleep between base and base+spread seconds,
  optionally capped with a max_sleep limit.
"""

import asyncio
import logging
import random
import time

logger = logging.getLogger(__name__)


def sleep_with_random_delay(
    base: float,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    *,
    max_sleep: float | None = None,
) -> None:
    """
    Sleep for a random duration by combining multiplicative and additive jitter.

    The total sleep time is computed as:

        duration = base * uniform(1.0, mul_spread) + uniform(0, add_spread)

    If `max_sleep` is provided, the duration will be capped at that value.

    :param base: Base sleep time in seconds. Must be >= 0.
    :param add_spread: Maximum extra seconds to add after scaling base.
    :param mul_spread: Maximum multiplier factor for base; drawn from [1.0, mul_spread].
    :param max_sleep: Optional upper limit for the final sleep duration.
    """
    if base < 0 or add_spread < 0 or mul_spread < 0:
        logger.warning(
            "[sleep] Invalid parameters: base=%s, add_spread=%s, mul_spread=%s",
            base,
            add_spread,
            mul_spread,
        )
        return

    # Calculate the raw duration
    multiplicative_jitter = random.uniform(1.0, mul_spread)
    additive_jitter = random.uniform(0, add_spread)
    duration = base * multiplicative_jitter + additive_jitter

    if max_sleep is not None:
        duration = min(duration, max_sleep)

    logger.debug("[time] Sleeping for %.2f seconds", duration)
    time.sleep(duration)
    return


async def async_sleep_with_random_delay(
    base: float,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    *,
    max_sleep: float | None = None,
) -> None:
    """
    Async sleep for a random duration by combining multiplicative and additive jitter.

    The total sleep time is computed as:

        duration = base * uniform(1.0, mul_spread) + uniform(0, add_spread)

    If `max_sleep` is provided, the duration will be capped at that value.

    :param base: Base sleep time in seconds. Must be >= 0.
    :param add_spread: Maximum extra seconds to add after scaling base.
    :param mul_spread: Maximum multiplier factor for base; drawn from [1.0, mul_spread].
    :param max_sleep: Optional upper limit for the final sleep duration.
    """
    if base < 0 or add_spread < 0 or mul_spread < 1.0:
        logger.warning(
            "[async sleep] Invalid parameters: base=%s, add_spread=%s, mul_spread=%s",
            base,
            add_spread,
            mul_spread,
        )
        return

    multiplicative_jitter = random.uniform(1.0, mul_spread)
    additive_jitter = random.uniform(0, add_spread)
    duration = base * multiplicative_jitter + additive_jitter

    if max_sleep is not None:
        duration = min(duration, max_sleep)

    logger.debug("[async time] Sleeping for %.2f seconds", duration)
    await asyncio.sleep(duration)


__all__ = ["sleep_with_random_delay", "async_sleep_with_random_delay"]
