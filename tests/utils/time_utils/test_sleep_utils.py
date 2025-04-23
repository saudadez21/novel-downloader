#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests.utils.time_utils.test_sleep_utils
---------------------------------------

Test suite for the `sleep_utils` module in `novel_downloader.utils.time_utils`.
Covers:
- Behavior with valid parameters, including default spread and optional max_sleep cap.
- Logging of info and warning messages.
- No sleep call on invalid (negative) parameters.
"""

import logging
import random
import time

import pytest

from novel_downloader.utils.time_utils.sleep_utils import sleep_with_random_delay


def test_negative_base_no_sleep_and_warning(caplog, monkeypatch):
    """
    Should warn and not sleep when base is negative.
    """
    caplog.set_level(logging.WARNING)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    sleep_with_random_delay(-1.0, 1.0)
    assert slept == []
    assert "[time] Invalid parameters: base=-1.0, spread=1.0" in caplog.text


def test_negative_spread_no_sleep_and_warning(caplog, monkeypatch):
    """
    Should warn and not sleep when spread is negative.
    """
    caplog.set_level(logging.WARNING)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    sleep_with_random_delay(1.0, -2.0)
    assert slept == []
    assert "[time] Invalid parameters: base=1.0, spread=-2.0" in caplog.text


def test_sleep_default_spread(monkeypatch, caplog):
    """
    Uses default spread=1.0 when not provided.
    """
    caplog.set_level(logging.INFO)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))
    # uniform should be called with (2.0, 3.0)
    monkeypatch.setattr(random, "uniform", lambda a, b: 2.5)

    sleep_with_random_delay(2.0)
    assert slept == [2.5]
    assert "[time] Sleeping for 2.50 seconds" in caplog.text


def test_sleep_without_max(monkeypatch, caplog):
    """
    Sleeps for the full random duration when no max_sleep is set.
    """
    caplog.set_level(logging.INFO)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))
    # base=2.0, spread=3.0 -> uniform range (2.0, 5.0)
    monkeypatch.setattr(random, "uniform", lambda a, b: a + (b - a) / 2)

    sleep_with_random_delay(2.0, 3.0)
    expected = 2.0 + (5.0 - 2.0) / 2  # =3.5
    assert slept == [pytest.approx(expected)]
    assert "[time] Sleeping for 3.50 seconds" in caplog.text


def test_sleep_with_max_sleep_capping(monkeypatch, caplog):
    """
    Caps the sleep duration at max_sleep when random.uniform returns larger.
    """
    caplog.set_level(logging.INFO)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(random, "uniform", lambda a, b: 10.0)

    sleep_with_random_delay(2.0, 3.0, max_sleep=4.0)
    assert slept == [4.0]
    assert "[time] Sleeping for 4.00 seconds" in caplog.text


def test_sleep_with_max_sleep_no_capping(monkeypatch, caplog):
    """
    Does not cap the sleep when random.uniform returns below max_sleep.
    """
    caplog.set_level(logging.INFO)
    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(random, "uniform", lambda a, b: 3.0)

    sleep_with_random_delay(2.0, 3.0, max_sleep=4.0)
    assert slept == [3.0]
    assert "[time] Sleeping for 3.00 seconds" in caplog.text
