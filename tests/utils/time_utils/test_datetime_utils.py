#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.time_utils.test_datetime_utils
-------------------------------------------

Test suite for the `datetime_utils` module in `novel_downloader.utils.time_utils`.
Covers:
- Parsing UTC offset strings into timezone objects.
- Calculating time differences between two datetime strings.
"""

import logging
from datetime import datetime, timedelta, timezone

import pytest

import novel_downloader.utils.time_utils.datetime_utils as dt_utils
from novel_downloader.utils.time_utils.datetime_utils import (
    _parse_utc_offset,
    calculate_time_difference,
)


@pytest.mark.parametrize(
    "tz_str, expected_offset",
    [
        # basic UTC
        ("UTC", timedelta(0)),
        ("utc", timedelta(0)),
        (" UTC ", timedelta(0)),
        # positive and negative offsets
        ("UTC+8", timedelta(hours=8)),
        ("UTC-05", timedelta(hours=-5)),
        ("utc+2", timedelta(hours=2)),
        ("UTC+00", timedelta(0)),
    ],
)
def test_parse_utc_offset_valid_variations(tz_str, expected_offset):
    """
    Should parse a variety of valid UTC offset strings correctly.
    """
    tz = _parse_utc_offset(tz_str)
    assert tz.utcoffset(None) == expected_offset


@pytest.mark.parametrize(
    "bad_str",
    [
        # wrong prefix
        "GMT+2",
        # missing sign or invalid number
        "UTC+abc",
        "UTC+-5",
        "UTC+5.5",
        # empty or whitespace-only
        "",
        "   ",
    ],
)
def test_parse_utc_offset_invalid(bad_str):
    """
    Should raise ValueError for malformed UTC offset strings.
    """
    with pytest.raises(ValueError):
        _parse_utc_offset(bad_str)


def test_calculate_time_difference_utc_to_utc():
    """
    Compute difference when both datetimes are in UTC.
    """
    # 2025-04-21 00:00:00 UTC -> 2025-04-22 01:02:03 UTC = 1d 1h 2m 3s
    days, hours, minutes, seconds = calculate_time_difference(
        "2025-04-21 00:00:00", "UTC", "2025-04-22 01:02:03", "UTC"
    )
    assert (days, hours, minutes, seconds) == (1, 1, 2, 3)


def test_calculate_time_difference_different_timezones():
    """
    Compute difference across time zones correctly.
    """
    # from 2025-04-21 00:00:00 UTC+8 (=> 2025-04-20 16:00:00 UTC)
    # to   2025-04-21 00:00:00 UTC   (=> 2025-04-21 00:00:00 UTC)
    # difference = 8 hours
    days, hours, minutes, seconds = calculate_time_difference(
        "2025-04-21 00:00:00", "UTC+8", "2025-04-21 00:00:00", "UTC"
    )
    assert (days, hours, minutes, seconds) == (0, 8, 0, 0)


def test_calculate_time_difference_reverse_order():
    """
    If `to_time` is before `from_time`, days should be negative.
    """
    days, hours, minutes, seconds = calculate_time_difference(
        "2025-04-22 00:00:00", "UTC", "2025-04-21 00:00:00", "UTC"
    )
    assert days == -1
    assert (hours, minutes, seconds) == (0, 0, 0)


def test_calculate_time_difference_invalid_inputs(caplog):
    """
    On any parsing error, should log a warning and return all zeros.
    """
    caplog.set_level(logging.WARNING)

    # invalid datetime format
    result = calculate_time_difference(
        "not-a-date", "UTC", "2025-04-22 00:00:00", "UTC"
    )
    assert result == (0, 0, 0, 0)
    assert "[time] Failed to calculate time difference" in caplog.text

    caplog.clear()

    # invalid timezone string
    result = calculate_time_difference(
        "2025-04-21 00:00:00", "GMT", "2025-04-22 00:00:00", "UTC"
    )
    assert result == (0, 0, 0, 0)
    assert "[time] Failed to calculate time difference" in caplog.text


def test_calculate_time_difference_default_to_time(monkeypatch):
    """
    When `to_time_str` is None, uses `datetime.now(timezone.utc)` internally.
    """
    # Freeze "now" at 2025-04-23 12:00:00 UTC
    fixed_now = datetime(2025, 4, 23, 12, 0, 0, tzinfo=timezone.utc)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    # Patch the module's datetime to our FixedDatetime
    monkeypatch.setattr(dt_utils, "datetime", FixedDatetime)

    # Calculate difference from 11:00 to fixed 12:00 => 1 hour
    days, hours, minutes, seconds = calculate_time_difference(
        "2025-04-23 11:00:00", "UTC"
    )
    assert (days, hours, minutes, seconds) == (0, 1, 0, 0)
