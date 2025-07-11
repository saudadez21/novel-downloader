#!/usr/bin/env python3
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
import re
from datetime import UTC, datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_DATETIME_FORMATS = [
    # ISO 8601
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "%Y-%m-%dT%H:%M:%SZ"),
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S%z"),
    # 完整年月日+时分秒 空格格式
    (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "%Y-%m-%d %H:%M:%S"),
    (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", "%Y-%m-%d %H:%M"),
    (r"\d{2}-\d{2}-\d{2} \d{2}:\d{2}", "%y-%m-%d %H:%M"),
    # 年月日 (无时间)
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    # Slashes 分隔
    (r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}", "%Y/%m/%d %H:%M:%S"),
    (r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}", "%Y/%m/%d %H:%M"),
    (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
    # 美式 MM/DD/YYYY [HH:MM[:SS] AM/PM]
    (
        r"\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}(:\d{2})? ?[APMapm]{2}",
        "%m/%d/%Y %I:%M:%S %p",
    ),
    (r"\d{1,2}/\d{1,2}/\d{4}", "%m/%d/%Y"),
    # 欧式 DD.MM.YYYY [HH:MM]
    (r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", "%d.%m.%Y %H:%M"),
    (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y"),
]


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
        except ValueError as err:
            raise ValueError(f"Invalid UTC offset hours: '{offset_part}'") from err
    return timezone(timedelta(hours=hours))


def _parse_datetime_flexible(dt_str: str) -> datetime:
    """
    Parse a date/time string in any of several common formats:

      • ISO 8601:             'YYYY-MM-DDTHH:MM:SSZ'
      • ISO w/ offset:        'YYYY-MM-DDTHH:MM:SS+HH:MM'
      • 'YYYY-MM-DD HH:MM:SS'
      • 'YYYY-MM-DD'          (time defaults to 00:00:00)
      • 'YYYY/MM/DD HH:MM:SS'
      • 'YYYY/MM/DD HH:MM'
      • 'YYYY/MM/DD'
      • 'MM/DD/YYYY HH:MM[:SS] AM/PM'
      • 'MM/DD/YYYY'
      • 'DD.MM.YYYY HH:MM'
      • 'DD.MM.YYYY'

    :param dt_str: Date/time string to parse.
    :return:       A naive datetime object.
    :raises ValueError: If dt_str does not match the expected formats.
    """
    s = dt_str.strip()
    for pattern, fmt in _DATETIME_FORMATS:
        if re.fullmatch(pattern, s):
            return datetime.strptime(s, fmt)

    supported = "\n".join(f"  • {fmt}" for _, fmt in _DATETIME_FORMATS)
    raise ValueError(
        f"Invalid date/time format: '{dt_str}'\n" f"Supported formats are:\n{supported}"
    )


def calculate_time_difference(
    from_time_str: str,
    tz_str: str = "UTC",
    to_time_str: str | None = None,
    to_tz_str: str = "UTC",
) -> tuple[int, int, int, int]:
    """
    Calculate the difference between two datetime values.

    :param from_time_str: Date-time string "YYYY-MM-DD HH:MM:SS" for the start.
    :param tz_str:        Timezone of from_time_str, e.g. 'UTC+8'. Defaults to 'UTC'.
    :param to_time_str:   Optional date-time string for the end; if None, uses now().
    :param to_tz_str:     Timezone of to_time_str. Defaults to 'UTC'.
    :return:              Tuple (days, hours, minutes, seconds).
    """
    try:
        # parse start time
        tz_from = _parse_utc_offset(tz_str)
        dt_from = _parse_datetime_flexible(from_time_str)
        dt_from = dt_from.replace(tzinfo=tz_from).astimezone(UTC)

        # parse end time or use now
        if to_time_str:
            tz_to = _parse_utc_offset(to_tz_str)
            dt_to = _parse_datetime_flexible(to_time_str)
            dt_to = dt_to.replace(tzinfo=tz_to).astimezone(UTC)
        else:
            dt_to = datetime.now(UTC)

        delta = dt_to - dt_from

        days = delta.days
        secs = delta.seconds
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60

        return days, hours, minutes, seconds

    except Exception as e:
        logger.warning("[time] Failed to calculate time difference: %s", e)
        return 999, 23, 59, 59


__all__ = [
    "calculate_time_difference",
]
