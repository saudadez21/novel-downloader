import asyncio

import pytest
from novel_downloader.libs.time_utils import (
    _calc_sleep_duration,
    async_jitter_sleep,
    jitter_sleep,
)

# ---------------------------
# _calc_sleep_duration tests
# ---------------------------


def test_calc_basic_range():
    """Duration should be within expected jitter range."""
    base = 1.0
    add = 0.5
    mul = 2.0
    for _ in range(20):
        d = _calc_sleep_duration(base, add, mul)
        assert d
        assert 1.0 <= d <= 1.0 * 2.0 + 0.5


def test_calc_with_max_sleep():
    """Should not exceed max_sleep."""
    d = _calc_sleep_duration(2.0, 1.0, 3.0, max_sleep=1.5)
    assert d
    assert d <= 1.5


@pytest.mark.parametrize(
    "base,add,mul",
    [
        (-1, 0, 1),  # negative base
        (1, -1, 1),  # negative add
        (1, 0, 0.5),  # mul_spread < 1
    ],
)
def test_calc_invalid_params(base, add, mul):
    assert _calc_sleep_duration(base, add, mul) is None


# ---------------------------
# jitter_sleep tests
# ---------------------------


def test_jitter_sleep_calls_time_sleep(monkeypatch):
    calls = {}

    def fake_sleep(x):
        calls["duration"] = x

    monkeypatch.setattr("time.sleep", fake_sleep)

    jitter_sleep(1.0, add_spread=0.2, mul_spread=1.5)

    # Should have called fake_sleep with some float
    assert "duration" in calls
    assert calls["duration"] >= 1.0


def test_jitter_sleep_invalid_params_no_sleep(monkeypatch):
    """Invalid params → no sleep() call."""
    called = {"sleep": False}

    def fake_sleep(_):
        called["sleep"] = True

    monkeypatch.setattr("time.sleep", fake_sleep)

    jitter_sleep(-1.0)  # invalid

    assert called["sleep"] is False


# ---------------------------
# async_jitter_sleep tests
# ---------------------------


@pytest.mark.asyncio
async def test_async_jitter_sleep_calls_asyncio_sleep(monkeypatch):
    called = {"duration": None}

    async def fake_sleep(x):
        called["duration"] = x

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await async_jitter_sleep(1.0, add_spread=0.3, mul_spread=1.2)

    assert called["duration"] is not None
    assert called["duration"] >= 1.0


@pytest.mark.asyncio
async def test_async_jitter_invalid_params(monkeypatch):
    called = {"sleep": False}

    async def fake_sleep(_):
        called["sleep"] = True

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await async_jitter_sleep(-2.0)  # invalid

    assert called["sleep"] is False
