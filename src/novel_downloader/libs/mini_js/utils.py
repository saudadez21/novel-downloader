#!/usr/bin/env python3
"""
novel_downloader.libs.mini_js.utils
-----------------------------------
"""

from __future__ import annotations

import re
from typing import Any, Final

ESCAPE_RE: Final[re.Pattern[str]] = re.compile(
    r"""
    \\(
        u\{[0-9a-fA-F]+\}   # \u{1F600}
      | u[0-9a-fA-F]{4}     # \u0041
      | x[0-9a-fA-F]{2}     # \x41
      | [nrtbfv0'"\\]       # \n \r \t \b \f \v \0 \' \" \\
      | .                   # unknown escape: keep the char (lenient)
    )
    """,
    re.VERBOSE,
)


def _escape_repl(m: re.Match[str]) -> str:
    s = m.group(1)
    try:
        if s.startswith("u{"):
            # \u{...}
            cp_hex = s[2:-1]
            return chr(int(cp_hex, 16))
        if s.startswith("u"):
            # \uFFFF
            return chr(int(s[1:], 16))
        if s.startswith("x"):
            # \xNN
            return chr(int(s[1:], 16))
        if s == "n":
            return "\n"
        if s == "r":
            return "\r"
        if s == "t":
            return "\t"
        if s == "b":
            return "\b"
        if s == "f":
            return "\f"
        if s == "v":
            return "\v"
        if s == "0":
            return "\0"
        if s in ("'", '"', "\\"):
            return s
        # unknown escape: lenient -> drop the backslash
        return s
    except Exception:
        # If anything goes wrong, keep the char
        return s


def unescape_js_string(quoted: str) -> str:
    """
    Parse JS string literal (supports \\xNN, \\uFFFF, \\u{...}).
    `quoted` includes quotes.
    """
    body = quoted[1:-1]
    if "\\" not in body:
        return body
    return ESCAPE_RE.sub(_escape_repl, body)


def to_int32(x: int | float) -> int:
    """ECMAScript ToInt32."""
    x = int(x) & 0xFFFFFFFF
    if x & 0x80000000:
        return -((~x + 1) & 0xFFFFFFFF)
    return x


def to_uint32(x: int | float) -> int:
    return int(x) & 0xFFFFFFFF


def js_truthy(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, int | float):
        return v != 0 and not (isinstance(v, float) and (v != v))
    if isinstance(v, str):
        return len(v) > 0
    return True


def js_nullish(v: Any) -> bool:
    # Map both JS null/undefined to Python None
    return v is None


def typeof_value(v: Any) -> str:
    if v is None:
        return "undefined"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int | float):
        return "number"
    if isinstance(v, str):
        return "string"
    return "object"
