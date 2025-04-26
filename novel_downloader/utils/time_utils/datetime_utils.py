#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.time_utils.datetime_utils
------------------------------------------------

Time utility functions for timezone-aware date calculations.

Includes:
- _parse_utc_offset():
    Converts UTC offset string (e.g. 'UTC+8') to a timezone object.
- calculate_time_difference():
    Computes timedelta between two datetime strings, with optional timezones.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _parse_utc_offset(tz_str: str) -> timezone:
    """
    Parse a timezone string like 'UTC+8' or 'UTC-5' into a datetime.timezone object.

    :param tz_str: Timezone in 'UTC±<hours>' format, e.g. 'UTC', 'UTC+8', 'UTC-05'
    :return:       Corresponding timezone object
    :raises ValueError: if tz_str is not a valid UTC offset format
    """
    tz_str_clean = tz_str.upper().strip()
    if not tz_str_clean.startswith("UTC"):
        raise ValueError(f"Timezone must start with 'UTC', got '{tz_str}'")
    offset_part = tz_str_clean[3:]
    if not offset_part:
        hours = 0
    else:
        try:
            hours = int(offset_part)
        except ValueError:
            raise ValueError(f"Invalid UTC offset hours: '{offset_part}'")
    return timezone(timedelta(hours=hours))


def calculate_time_difference(
    from_time_str: str,
    tz_str: str = "UTC",
    to_time_str: Optional[str] = None,
    to_tz_str: str = "UTC",
) -> Tuple[int, int, int, int]:
    """
    Calculate the difference between two datetime values.

    :param from_time_str: Date‐time string "YYYY‑MM‑DD HH:MM:SS" for the start.
    :param tz_str:        Timezone of from_time_str, e.g. 'UTC+8'. Defaults to 'UTC'.
    :param to_time_str:   Optional date‐time string for the end; if None, uses now().
    :param to_tz_str:     Timezone of to_time_str. Defaults to 'UTC'.
    :return:              Tuple (days, hours, minutes, seconds).
    """
    try:
        # parse start time
        tz_from = _parse_utc_offset(tz_str)
        dt_from = datetime.strptime(from_time_str, "%Y-%m-%d %H:%M:%S")
        dt_from = dt_from.replace(tzinfo=tz_from).astimezone(timezone.utc)

        # parse end time or use now
        if to_time_str:
            tz_to = _parse_utc_offset(to_tz_str)
            dt_to = datetime.strptime(to_time_str, "%Y-%m-%d %H:%M:%S")
            dt_to = dt_to.replace(tzinfo=tz_to).astimezone(timezone.utc)
        else:
            dt_to = datetime.now(timezone.utc)

        delta = dt_to - dt_from

        days = delta.days
        secs = delta.seconds
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60

        return days, hours, minutes, seconds

    except Exception as e:
        logger.warning("[time] Failed to calculate time difference: %s", e)
        return 0, 0, 0, 0


__all__ = [
    "calculate_time_difference",
]
