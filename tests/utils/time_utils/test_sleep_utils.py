#!/usr/bin/env python3
"""
tests.utils.time_utils.test_sleep_utils
---------------------------------------

Test suite for the `sleep_utils` module in `novel_downloader.utils.time_utils`.

Covers:
- Handling of invalid (negative) parameters.
- Correct duration computation for:
    • default spreads,
    • additive-only jitter,
    • multiplicative-only jitter,
    • combined additive + multiplicative jitter.
- Enforcement of `max_sleep` cap.
- Proper logging of warnings and info messages.
"""

import logging
import random
import time

import pytest

from novel_downloader.utils.time_utils.sleep_utils import sleep_with_random_delay


def test_negative_parameters_warn_and_no_sleep(caplog, monkeypatch):
    """
    When any of base, add_spread, or mul_spread is negative,
    the function should log a single WARNING and perform no sleep.
    """
    caplog.set_level(logging.WARNING)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # Negative base
    sleep_with_random_delay(-1.0, add_spread=0.5, mul_spread=1.2)
    assert slept == []
    assert (
        "[sleep] Invalid parameters: base=-1.0, add_spread=0.5, mul_spread=1.2"
        in caplog.text
    )

    caplog.clear()

    # Negative add_spread
    sleep_with_random_delay(1.0, add_spread=-0.5, mul_spread=1.2)
    assert slept == []
    assert (
        "[sleep] Invalid parameters: base=1.0, add_spread=-0.5, mul_spread=1.2"
        in caplog.text
    )

    caplog.clear()

    # Negative mul_spread
    sleep_with_random_delay(1.0, add_spread=0.5, mul_spread=-1.0)
    assert slept == []
    assert (
        "[sleep] Invalid parameters: base=1.0, add_spread=0.5, mul_spread=-1.0"
        in caplog.text
    )


def test_default_spreads(monkeypatch, caplog):
    """
    With only `base` provided, `add_spread` defaults to 0.0 and
    `mul_spread` defaults to 1.0, so duration == base exactly.
    """
    caplog.set_level(logging.INFO)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # uniform(1.0, 1.0) -> 1.0; uniform(0, 0.0) -> 0.0
    def fake_uniform(a, b):
        if (a, b) == (1.0, 1.0):
            return 1.0
        if (a, b) == (0, 0.0):
            return 0.0
        pytest.skip(f"Unexpected uniform args: {a!r}, {b!r}")

    monkeypatch.setattr(random, "uniform", fake_uniform)

    sleep_with_random_delay(2.5)
    assert slept == [2.5]
    assert "[time] Sleeping for 2.50 seconds" in caplog.text


def test_additive_only_jitter(monkeypatch, caplog):
    """
    When `add_spread` > 0 and `mul_spread` == 1.0,
    only the additive jitter contributes beyond base.
    """
    caplog.set_level(logging.INFO)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # multiplicative_jitter = 1.0
    # additive_jitter = 1.5
    calls = []

    def fake_uniform(a, b):
        calls.append((a, b))
        if a == 1.0 and b == 1.0:
            return 1.0
        if a == 0 and b == 3.0:
            return 1.5
        pytest.skip(f"Unexpected uniform args: {a}, {b}")

    monkeypatch.setattr(random, "uniform", fake_uniform)

    sleep_with_random_delay(2.0, add_spread=3.0, mul_spread=1.0)
    expected = 2.0 * 1.0 + 1.5
    assert slept == [pytest.approx(expected)]
    assert "[time] Sleeping for 3.50 seconds" in caplog.text


def test_multiplicative_only_jitter(monkeypatch, caplog):
    """
    When `mul_spread` > 1.0 and `add_spread` == 0.0,
    only the multiplicative jitter scales the base.
    """
    caplog.set_level(logging.INFO)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # multiplicative_jitter = 1.2
    # additive_jitter = 0.0
    def fake_uniform(a, b):
        if a == 1.0 and b == 1.5:
            return 1.2
        if a == 0 and b == 0.0:
            return 0.0
        pytest.skip(f"Unexpected uniform args: {a}, {b}")

    monkeypatch.setattr(random, "uniform", fake_uniform)

    sleep_with_random_delay(2.0, add_spread=0.0, mul_spread=1.5)
    expected = 2.0 * 1.2 + 0.0
    assert slept == [pytest.approx(expected)]
    assert "[time] Sleeping for 2.40 seconds" in caplog.text


def test_combined_jitter(monkeypatch, caplog):
    """
    When both `mul_spread` and `add_spread` > 1, duration uses both jitters.
    """
    caplog.set_level(logging.INFO)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # multiplicative_jitter = 1.1
    # additive_jitter = 0.7
    def fake_uniform(a, b):
        if (a, b) == (1.0, 2.0):
            return 1.1
        if (a, b) == (0, 1.0):
            return 0.7
        pytest.skip(f"Unexpected uniform args: {a}, {b}")

    monkeypatch.setattr(random, "uniform", fake_uniform)

    sleep_with_random_delay(3.0, add_spread=1.0, mul_spread=2.0)
    expected = 3.0 * 1.1 + 0.7
    assert slept == [pytest.approx(expected)]
    assert "[time] Sleeping for %.2f seconds" % expected in caplog.text


def test_max_sleep_cap(monkeypatch, caplog):
    """
    When computed duration exceeds `max_sleep`, the sleep time is capped.
    """
    caplog.set_level(logging.INFO)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # Force a large jitter: multiplicative_jitter=5.0, additive_jitter=2.0
    def fake_uniform(a, b):
        return 5.0 if a == 1.0 else 2.0

    monkeypatch.setattr(random, "uniform", fake_uniform)

    sleep_with_random_delay(1.0, add_spread=2.0, mul_spread=5.0, max_sleep=3.0)
    assert slept == [3.0]
    assert "[time] Sleeping for 3.00 seconds" in caplog.text


def test_max_sleep_no_cap(monkeypatch, caplog):
    """
    When computed duration is below `max_sleep`, no capping is applied.
    """
    caplog.set_level(logging.INFO)

    slept = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    # Force moderate jitter: multiplicative_jitter=1.5, additive_jitter=0.5
    def fake_uniform(a, b):
        if a == 1.0:
            return 1.5
        return 0.5

    monkeypatch.setattr(random, "uniform", fake_uniform)

    sleep_with_random_delay(2.0, add_spread=1.0, mul_spread=1.5, max_sleep=5.0)
    expected = 2.0 * 1.5 + 0.5
    assert slept == [pytest.approx(expected)]
    assert "[time] Sleeping for %.2f seconds" % expected in caplog.text
