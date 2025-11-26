import random

import pytest

from novel_downloader.libs.textutils.numbers import (
    arabic_to_chinese,
    chinese_to_arabic,
)


# -------------------------
# Basic correctness tests
# -------------------------
@pytest.mark.parametrize(
    "s,expected",
    [
        ("零", 0),
        ("一", 1),
        ("十", 10),
        ("十一", 11),
        ("二十", 20),
        ("二十一", 21),
        ("一百零三", 103),
        ("一百二十三", 123),
        ("一千二百三十四", 1234),
        ("一万", 10000),
        ("一万零三", 10003),
        ("一万五千", 15000),
        ("三亿二千五百", 300002500),
        ("兆一", 1_000_000_000_000 + 1),
        ("一京零三", 10**16 + 3),
        ("一垓二千三百", 10**20 + 2300),
        ("负一千二百三十四", -1234),
        ("-一万五千", -15000),
    ],
)
def test_chinese_to_arabic_basic(s, expected):
    assert chinese_to_arabic(s) == expected


# -------------------------
# arabic_to_chinese basic tests
# -------------------------
@pytest.mark.parametrize(
    "num,expected",
    [
        (0, "零"),
        (1, "一"),
        (10, "十"),
        (11, "十一"),
        (20, "二十"),
        (21, "二十一"),
        (103, "一百零三"),
        (123, "一百二十三"),
        (1234, "一千二百三十四"),
        # (10003, "一万零三"),
        (15000, "一万五千"),
        (-1234, "负一千二百三十四"),
        (-205, "负二百零五"),
    ],
)
def test_arabic_to_chinese_basic(num, expected):
    assert arabic_to_chinese(num) == expected


# -------------------------
# Round-trip: 0 - 9999
# -------------------------
def test_roundtrip_small_range():
    for i in range(10000):
        s = arabic_to_chinese(i)
        r = chinese_to_arabic(s)
        assert r == i, f"Round-trip failed: {i} -> {s} -> {r}"


# -------------------------
# Random large round-trip tests
# -------------------------
@pytest.mark.parametrize("exp", range(5, 18))  # 10^5 ... 10^18
def test_roundtrip_large_numbers(exp):
    lower = 10**exp
    upper = 10 ** (exp + 1)

    for _ in range(3):  # try 3 random values per exponent
        n = random.randint(lower, upper - 1)

        for val in (n, -n):
            s = arabic_to_chinese(val)
            r = chinese_to_arabic(s)
            assert r == val, f"Large round-trip failed: {val} -> {s} -> {r}"


# -------------------------
# Error handling
# -------------------------
def test_chinese_to_arabic_empty():
    with pytest.raises(ValueError):
        chinese_to_arabic("")


def test_arabic_to_chinese_type_error():
    with pytest.raises(TypeError):
        arabic_to_chinese("123")  # must be int


def test_chinese_to_arabic_invalid_char():
    with pytest.raises(KeyError):
        chinese_to_arabic("三千ABC")
