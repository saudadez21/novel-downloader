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
        num = 0
        section_total = 0
        for ch in sec:
            if ch in CHINESE_NUMERALS:
                num = num * 10 + CHINESE_NUMERALS[ch]
            else:
                unit = CHINESE_UNITS[ch]
                section_total += (num or 1) * unit
                num = 0
        return section_total + num

    total = 0
    rest = s
    for char, val in LARGE_UNITS:
        if char in rest:
            left, rest = rest.split(char, 1)
            total += _parse_section(left) * val

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
        """
        Convert a value 1..9999 into Chinese using 千/百/十 units,
        without any large unit (万, 亿, ...) or leading '零'.
        """
        s = ""
        unit_pos = 0
        zero_flag = True
        while sec > 0:
            d = sec % 10
            if d == 0:
                # only emit one '零' for consecutive zeros
                if not zero_flag:
                    s = digits[0] + s
                    zero_flag = True
            else:
                s = digits[d] + small_units[unit_pos] + s
                zero_flag = False
            unit_pos += 1
            sec //= 10
        return s

    result = ""
    section_pos = 0

    while num > 0:
        section = num % 10_000
        if section != 0:
            sec_str = _section_to_chinese(section)
            result = sec_str + big_units[section_pos] + result
        else:
            # if there's already something in `result`, and the next non-zero
            # block will appear further left, we need a '零' separator
            if result and not result.startswith("零"):
                result = "零" + result

        num //= 10_000
        section_pos += 1

    if negative:
        result = "负" + result

    return result


if __name__ == "__main__":
    import random

    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"
    random.seed(42)

    fail_count = 0
    num_list = [
        ("一千二百三十四", 1234),
        ("一万五千", 15000),
        ("一万零三", 10003),
        ("三亿二千五百", 300002500),
    ]
    print("=== chinese_to_arabic() with fixed cases ===")
    for s, expected in num_list:
        actual = chinese_to_arabic(s)
        if actual != expected:
            print(f"{RED}FAIL:{RESET} “{s}” -> expected {expected}, got {actual}")
            fail_count += 1

    if fail_count:
        print(f"{RED}{fail_count} chinese_to_arabic() tests failed.{RESET}\n")
    else:
        print(f"{GREEN}All {len(num_list)} chinese_to_arabic() tests passed!{RESET}\n")

    fail_count = 0
    print("=== Round-trip test for values 0 - 9999 ===")
    for i in range(10_000):
        s = arabic_to_chinese(i)
        r = chinese_to_arabic(s)
        if r != i:
            print(f'{RED}FAIL round-trip:{RESET} {i} -> "{s}" -> {r}')
            fail_count += 1
            break

    if fail_count:
        print(f"{RED}{fail_count} round-trip failures in 0 - 9999.{RESET}\n")
    else:
        print(f"{GREEN}0 - 9999 round-trip all passed!{RESET}\n")

    fail_count = 0
    exponents = range(5, 22)  # test around 10^5...
    print("=== Random round-trip at larger scales ===")
    for exp in exponents:
        lower = 10**exp
        upper = 10 ** (exp + 1)
        for _ in range(2):
            i = random.randint(lower, upper - 1)
            for val in (i, -i):
                s = arabic_to_chinese(val)
                r = chinese_to_arabic(s)
                if r != val:
                    print(f'{RED}FAIL:{RESET} {val} -> "{s}" -> {r}')
                    fail_count += 1

    if fail_count:
        print(f"{RED}{fail_count} random large-scale failures.{RESET}")
    else:
        print(f"{GREEN}All random large-scale round-trips passed!{RESET}")
