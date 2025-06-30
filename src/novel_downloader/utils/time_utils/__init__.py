#!/usr/bin/env python3
"""
novel_downloader.utils.time_utils
---------------------------------

Utility functions for time and date-related operations.

Includes:
- calculate_time_difference:
    Computes time delta between two timezone-aware datetime strings.
- sleep_with_random_delay:
    Sleeps for a random duration, useful for human-like delays or rate limiting.
"""

from .datetime_utils import calculate_time_difference
from .sleep_utils import async_sleep_with_random_delay, sleep_with_random_delay

__all__ = [
    "calculate_time_difference",
    "async_sleep_with_random_delay",
    "sleep_with_random_delay",
]
