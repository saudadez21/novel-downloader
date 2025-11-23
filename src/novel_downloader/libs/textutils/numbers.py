#!/usr/bin/env python3
"""
novel_downloader.libs.textutils.numbers
---------------------------------------

Utility functions to convert between Chinese numeral strings
and Python integers.
"""

CHINESE_NUMERALS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "壹": 1,
    "二": 2,
    "两": 2,
    "贰": 2,
    "貮": 2,
    "三": 3,
    "叁": 3,
    "四": 4,
    "肆": 4,
    "五": 5,
    "伍": 5,
    "六": 6,
    "陆": 6,
    "七": 7,
    "柒": 7,
    "八": 8,
    "捌": 8,
    "九": 9,
    "玖": 9,
}

CHINESE_UNITS = {
    "十": 10,
    "拾": 10,
    "百": 100,
    "佰": 100,
    "千": 1000,
    "仟": 1000,
    "万": 10_000,
    "萬": 10_000,
    "亿": 100_000_000,
    "億": 100_000_000,
    "兆": 10**12,
    "京": 10**16,
    "垓": 10**20,
}

LARGE_UNITS = [
    ("垓", 10**20),
    ("京", 10**16),
    ("兆", 10**12),
    ("亿", 10**8),
    ("億", 10**8),
    ("万", 10**4),
    ("萬", 10**4),
]


def chinese_to_arabic(s: str) -> int:
    """
    Convert a Chinese numeral string into its integer value.

    Examples:
    ---
    >>> chinese_to_arabic("一千二百三十四")
    1234
    >>> chinese_to_arabic("负一千二百三十四")
    -1234
    >>> chinese_to_arabic("一万零三")
    10003
    >>> chinese_to_arabic("三亿二千五百")
    3000002500

    :param s: A string of Chinese numerals, e.g. "三千零二十一", "五亿零七万".
    :return: The integer value represented by the input string.
    :raises KeyError: If `s` contains characters not found in the supported
                      numeral or unit mappings.
    """
    if not s:
        raise ValueError("Input string is empty")

    sign = 1
    if s[0] in ("负", "-"):
        sign = -1
        s = s[1:]

    def _parse_section(sec: str) -> int:
        """Parse up to 千 unit."""
        if not sec:
            return 0

        num = 0
        total = 0

        for ch in sec:
            if ch in CHINESE_NUMERALS:
                num = num * 10 + CHINESE_NUMERALS[ch]
            else:
                unit = CHINESE_UNITS[ch]
                total += (num or 1) * unit
                num = 0

        return total + num

    total = 0
    rest = s

    for char, val in LARGE_UNITS:
        if char in rest:
            left, rest = rest.split(char, 1)
            left_val = _parse_section(left) if left else 1
            total += left_val * val

    total += _parse_section(rest)

    return sign * total


def arabic_to_chinese(num: int) -> str:
    """
    Convert an integer to its Chinese numeral representation.

    Examples:
    ---
    >>> arabic_to_chinese(0)
    "零"
    >>> arabic_to_chinese(1234)
    "一千二百三十四"
    >>> arabic_to_chinese(10003)
    "一万零三"
    >>> arabic_to_chinese(-205)
    "负二百零五"
    >>> arabic_to_chinese(3000002500)
    "三十亿零二百五百"  # 3 000 002 500

    :param num: The integer to convert (e.g. 42, -1300).
    :return: The Chinese-numeral string for `num`.
    :raises TypeError: If `num` is not an integer.
    """
    if not isinstance(num, int):
        raise TypeError("Input must be an integer.")
    if num == 0:
        return "零"

    digits = "零一二三四五六七八九"
    small_units = ["", "十", "百", "千"]
    big_units = ["", "万", "亿", "兆", "京", "垓"]

    negative = num < 0
    num = -num if negative else num

    def _section_to_chinese(sec: int) -> str:
        """Convert 1..9999 into Chinese without big units."""
        s = ""
        unit_pos = 0
        zero_flag = True

        while sec > 0:
            d = sec % 10
            if d == 0:
                if not zero_flag:
                    s = "零" + s
                    zero_flag = True
            else:
                s = digits[d] + small_units[unit_pos] + s
                zero_flag = False
            unit_pos += 1
            sec //= 10

        return s

    parts: list[str] = []
    section_pos = 0
    need_zero = False

    while num > 0:
        sec = num % 10_000
        if sec == 0:
            if parts:
                need_zero = True
        else:
            sec_str = _section_to_chinese(sec)
            if need_zero:
                parts.append("零")
                need_zero = False
            parts.append(sec_str + big_units[section_pos])
        num //= 10_000
        section_pos += 1

    result = "".join(reversed(parts))

    if result.startswith("一十") and len(result) > 2:
        result = result[1:]
    elif result == "一十":
        result = "十"

    if negative:
        result = "负" + result

    return result
