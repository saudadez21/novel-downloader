#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.time_utils.sleep_utils
---------------------------------------------

Utilities for adding randomized delays in scripts and bots.

Includes:
- sleep_with_random_delay(): Sleep between base and base+spread seconds,
  optionally capped with a max_sleep limit.
"""

import logging
import random
import time
from typing import Optional

logger = logging.getLogger(__name__)


def sleep_with_random_delay(
    base: float, spread: float = 1.0, *, max_sleep: Optional[float] = None
) -> None:
    """
    Sleep for a random duration between `base` and `base + spread`,
    optionally capped by `max_sleep`.

    Useful for simulating human-like behavior or preventing rate-limiting
    issues in scripts.

    :param base: Minimum number of seconds to sleep.
    :param spread: Maximum extra seconds to add on top of base (default: 1.0).
    :param max_sleep: Optional upper limit for the total sleep duration.
    """
    if base < 0 or spread < 0:
        logger.warning("[time] Invalid parameters: base=%s, spread=%s", base, spread)
        return

    duration = random.uniform(base, base + spread)
    if max_sleep is not None:
        duration = min(duration, max_sleep)

    logger.info("[time] Sleeping for %.2f seconds", duration)
    time.sleep(duration)
    return


__all__ = ["sleep_with_random_delay"]
