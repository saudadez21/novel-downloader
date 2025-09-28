#!/usr/bin/env python3
"""
novel_downloader.libs.time_utils
--------------------------------

Utilities for adding randomized delays in scripts and bots.
"""

__all__ = ["jitter_sleep", "async_jitter_sleep"]

import asyncio
import logging
import random
import time

logger = logging.getLogger(__name__)


def _calc_sleep_duration(
    base: float,
    add_spread: float,
    mul_spread: float,
    max_sleep: float | None = None,
    *,
    log_prefix: str = "sleep",
) -> float | None:
    """
    Compute the jittered sleep duration (in seconds) or return None if params invalid.

      duration = base * uniform(1.0, mul_spread) + uniform(0, add_spread)

    then optionally capped by max_sleep.
    """
    if base < 0 or add_spread < 0 or mul_spread < 1.0:
        logger.warning(
            "%s: Invalid parameters (base=%s, add_spread=%s, mul_spread=%s)",
            log_prefix,
            base,
            add_spread,
            mul_spread,
        )
        return None

    multiplicative_jitter = random.uniform(1.0, mul_spread)
    additive_jitter = random.uniform(0.0, add_spread)
    duration = base * multiplicative_jitter + additive_jitter

    if max_sleep is not None:
        duration = min(duration, max_sleep)

    logger.debug(
        "%s: base=%.3f mul=%.3f add=%.3f max=%s -> duration=%.3f",
        log_prefix,
        base,
        multiplicative_jitter,
        additive_jitter,
        max_sleep,
        duration,
    )
    return duration


def jitter_sleep(
    base: float,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    *,
    max_sleep: float | None = None,
) -> None:
    """
    Sleep for a random duration by combining multiplicative and additive jitter.

    :param base: Base sleep time in seconds. Must be >= 0.
    :param add_spread: Maximum extra seconds to add after scaling base.
    :param mul_spread: Maximum multiplier factor for base; drawn from [1.0, mul_spread].
    :param max_sleep: Optional upper limit for the final sleep duration.
    """
    duration = _calc_sleep_duration(
        base,
        add_spread,
        mul_spread,
        max_sleep,
        log_prefix="sleep",
    )
    if duration is None:
        return
    time.sleep(duration)


async def async_jitter_sleep(
    base: float,
    add_spread: float = 0.0,
    mul_spread: float = 1.0,
    *,
    max_sleep: float | None = None,
) -> None:
    """
    Async sleep for a random duration by combining multiplicative and additive jitter.

    :param base: Base sleep time in seconds. Must be >= 0.
    :param add_spread: Maximum extra seconds to add after scaling base.
    :param mul_spread: Maximum multiplier factor for base; drawn from [1.0, mul_spread].
    :param max_sleep: Optional upper limit for the final sleep duration.
    """
    duration = _calc_sleep_duration(
        base, add_spread, mul_spread, max_sleep, log_prefix="async sleep"
    )
    if duration is None:
        return
    await asyncio.sleep(duration)
