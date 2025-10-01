#!/usr/bin/env python3
"""
novel_downloader.libs.mini_js.tokenizer
---------------------------------------
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Final

# ============================================================
# Token kind constants (small ints)
# ============================================================

T_EOF = 0

# numbers & strings
T_FLOAT = 1
T_INTEGER = 2
T_STRING = 3

# identifiers & keywords
T_ID = 10
T_INF = 11
T_NAN = 12
T_NULL = 13
T_UNDEF = 14
T_TRUE = 15
T_FALSE = 16
T_LET = 17
T_RETURN = 18
T_FUNCTION = 19
T_TYPEOF = 20
T_DELETE = 21
T_IN = 22

# multi-char operators
T_SHREQ = 30  # >>>=
T_SHR = 31  # >>>
T_SAREQ = 32  # >>=
T_SAR = 33  # >>
T_SHLEQ = 34  # <<=
T_SHL = 35  # <<
T_POWEQ = 36  # **=
T_POW = 37  # **
T_NULLISHEQ = 38  # ??=
T_QDOT = 39  # ?.
T_NULLISH = 40  # ??
T_OROREQ = 41  # ||=
T_ANDANDEQ = 42  # &&=
T_ANDEQ = 43  # &=
T_OREQ = 44  # |=
T_XOREQ = 45  # ^=
T_PLUSEQ = 46
T_MINUSEQ = 47
T_TIMESEQ = 48
T_DIVEQ = 49
T_MODEQ = 50
T_SEQ = 51  # ===
T_SNEQ = 52  # !==
T_LE = 53  # <=
T_GE = 54  # >=
T_EQEQ = 55  # ==
T_NEQ = 56  # !=
T_ANDAND = 57  # &&
T_OROR = 58  # ||

# single-char punctuation / ops
T_QUESTION = 70  # ?
T_DOT = 71  # .
T_NOT = 72  # !  (also keyword 'not' maps here)

T_LBRACE = 80
T_RBRACE = 81
T_LPAREN = 82
T_RPAREN = 83
T_LBRACK = 84
T_RBRACK = 85
T_COMMA = 86
T_COLON = 87
T_SEMICOL = 88
T_PLUS = 89
T_MINUS = 90
T_TIMES = 91
T_DIV = 92
T_MOD = 93
T_AMP = 94
T_BAR = 95
T_CARET = 96
T_TILDE = 97
T_LT = 98
T_GT = 99
T_EQ = 100


@dataclass(slots=True)
class Token:
    type: int
    value: str


# --------- helpers (fast ASCII checks) ---------

_DIGIT = tuple(chr(i).isdigit() for i in range(128))
_UPPER = tuple("A" <= chr(i) <= "Z" for i in range(128))
_LOWER = tuple("a" <= chr(i) <= "z" for i in range(128))
_ASCII = tuple(i < 128 for i in range(256))  # guard
_WS = set(" \t\r\n")


def _is_hex(ch: str) -> bool:
    o = ord(ch)
    return (48 <= o <= 57) or (65 <= o <= 70) or (97 <= o <= 102)


def _is_ident_start_fast(ch: str) -> bool:
    oc = ord(ch)
    if oc < 128:
        return _UPPER[oc] or _LOWER[oc] or ch == "_" or ch == "$"
    return False  # non-ASCII start in this subset handled via \uXXXX escape


def _is_ident_part_fast(ch: str) -> bool:
    oc = ord(ch)
    if oc < 128:
        return _UPPER[oc] or _LOWER[oc] or _DIGIT[oc] or ch in ("_", "$")
    return False


def _read_ident(code: str, i: int, n: int) -> tuple[str, int]:
    """Read identifier with ASCII fast path + \\uXXXX escapes."""
    j = i
    while j < n:
        ch = code[j]
        if ch == "\\":
            # \uXXXX
            if (
                j + 5 < n
                and code[j + 1] == "u"
                and all(_is_hex(c) for c in code[j + 2 : j + 6])
            ):
                j += 6
                continue
            break
        if not _is_ident_part_fast(ch):
            break
        j += 1
    return code[i:j], j


def _read_number(code: str, i: int, n: int) -> tuple[int, str, int]:
    j = i
    saw_dot = False
    saw_exp = False

    if code[j] == ".":
        saw_dot = True
        j += 1
        while j < n and code[j].isdigit():
            j += 1
    else:
        while j < n and code[j].isdigit():
            j += 1
        if j < n and code[j] == ".":
            saw_dot = True
            j += 1
            while j < n and code[j].isdigit():
                j += 1

    if j < n and (code[j] in "eE"):
        k = j + 1
        if k < n and code[k] in "+-":
            k += 1
        if k < n and code[k].isdigit():
            saw_exp = True
            j = k + 1
            while j < n and code[j].isdigit():
                j += 1

    kind = T_FLOAT if (saw_dot or saw_exp) else T_INTEGER
    return kind, code[i:j], j


def _read_string(code: str, i: int, n: int) -> tuple[str, int]:
    quote = code[i]
    j = i + 1
    while j < n:
        ch = code[j]
        if ch == "\\":
            j += 2
            continue
        if ch == quote:
            j += 1
            break
        j += 1
    return code[i:j], j


class JsTokenizer:
    _KW: Final[dict[str, int]] = {
        "Infinity": T_INF,
        "NaN": T_NAN,
        "null": T_NULL,
        "undefined": T_UNDEF,
        "true": T_TRUE,
        "false": T_FALSE,
        "let": T_LET,
        "return": T_RETURN,
        "function": T_FUNCTION,
        "typeof": T_TYPEOF,
        "delete": T_DELETE,
        "in": T_IN,
        "not": T_NOT,  # map to NOT
    }

    def __init__(self) -> None:
        pass

    def tokenize(self, code: str) -> Iterator[Token]:
        n = len(code)
        i = 0
        emit = Token

        while i < n:
            ch = code[i]

            # whitespace
            if ch in _WS:
                i += 1
                while i < n and code[i] in _WS:
                    i += 1
                continue

            # comments and '/' handling
            if ch == "/":
                if i + 1 < n:
                    b = code[i + 1]
                    if b == "/":
                        i += 2
                        while i < n and code[i] != "\n":
                            i += 1
                        continue
                    if b == "*":
                        i += 2
                        # scan until '*/'
                        while i + 1 < n and not (code[i] == "*" and code[i + 1] == "/"):
                            i += 1
                        i = min(n, i + 2)
                        continue
                    if b == "=":
                        yield emit(T_DIVEQ, "/=")
                        i += 2
                        continue
                yield emit(T_DIV, "/")
                i += 1
                continue

            # numbers
            if ch.isdigit() or (ch == "." and i + 1 < n and code[i + 1].isdigit()):
                kind, val, j = _read_number(code, i, n)
                yield emit(kind, val)
                i = j
                continue

            # strings
            if ch == '"' or ch == "'":
                val, j = _read_string(code, i, n)
                yield emit(T_STRING, val)
                i = j
                continue

            # identifiers / keywords
            if ch == "\\":
                # only support \uXXXX escapes in identifiers
                if (
                    i + 5 < n
                    and code[i + 1] == "u"
                    and all(_is_hex(c) for c in code[i + 2 : i + 6])
                ):
                    ident, j = _read_ident(code, i, n)
                    yield emit(self._KW.get(ident, T_ID), ident)
                    i = j
                    continue
            elif _is_ident_start_fast(ch):
                ident, j = _read_ident(code, i, n)
                yield emit(self._KW.get(ident, T_ID), ident)
                i = j
                continue

            # ------ operators: hand-written matching (no slicing) ------
            # 4-char
            if (
                ch == ">"
                and i + 3 < n
                and code[i + 1] == ">"
                and code[i + 2] == ">"
                and code[i + 3] == "="
            ):
                yield emit(T_SHREQ, ">>>=")
                i += 4
                continue

            # 3-char
            if i + 2 < n:
                b1 = code[i + 1]
                b2 = code[i + 2]
                if ch == ">" and b1 == ">" and b2 == ">":
                    yield emit(T_SHR, ">>>")
                    i += 3
                    continue
                if ch == ">" and b1 == ">" and b2 == "=":
                    yield emit(T_SAREQ, ">>=")
                    i += 3
                    continue
                if ch == "<" and b1 == "<" and b2 == "=":
                    yield emit(T_SHLEQ, "<<=")
                    i += 3
                    continue
                if ch == "*" and b1 == "*" and b2 == "=":
                    yield emit(T_POWEQ, "**=")
                    i += 3
                    continue
                if ch == "?" and b1 == "?" and b2 == "=":
                    yield emit(T_NULLISHEQ, "??=")
                    i += 3
                    continue
                if ch == "&" and b1 == "&" and b2 == "=":
                    yield emit(T_ANDANDEQ, "&&=")
                    i += 3
                    continue
                if ch == "|" and b1 == "|" and b2 == "=":
                    yield emit(T_OROREQ, "||=")
                    i += 3
                    continue
                if ch == "=" and b1 == "=" and b2 == "=":
                    yield emit(T_SEQ, "===")
                    i += 3
                    continue
                if ch == "!" and b1 == "=" and b2 == "=":
                    yield emit(T_SNEQ, "!==")
                    i += 3
                    continue

            # 2-char
            if i + 1 < n:
                b = code[i + 1]
                if ch == "=" and b == "=":
                    yield emit(T_EQEQ, "==")
                    i += 2
                    continue
                if ch == "!" and b == "=":
                    yield emit(T_NEQ, "!=")
                    i += 2
                    continue
                if ch == "<" and b == "=":
                    yield emit(T_LE, "<=")
                    i += 2
                    continue
                if ch == ">" and b == "=":
                    yield emit(T_GE, ">=")
                    i += 2
                    continue
                if ch == "&" and b == "&":
                    yield emit(T_ANDAND, "&&")
                    i += 2
                    continue
                if ch == "|" and b == "|":
                    yield emit(T_OROR, "||")
                    i += 2
                    continue
                if ch == "?" and b == ".":
                    yield emit(T_QDOT, "?.")
                    i += 2
                    continue
                if ch == "?" and b == "?":
                    yield emit(T_NULLISH, "??")
                    i += 2
                    continue
                if ch == "<" and b == "<":
                    yield emit(T_SHL, "<<")
                    i += 2
                    continue
                if ch == ">" and b == ">":
                    yield emit(T_SAR, ">>")
                    i += 2
                    continue
                if ch == "*" and b == "*":
                    yield emit(T_POW, "**")
                    i += 2
                    continue
                if ch == "+" and b == "=":
                    yield emit(T_PLUSEQ, "+=")
                    i += 2
                    continue
                if ch == "-" and b == "=":
                    yield emit(T_MINUSEQ, "-=")
                    i += 2
                    continue
                if ch == "*" and b == "=":
                    yield emit(T_TIMESEQ, "*=")
                    i += 2
                    continue
                if ch == "%" and b == "=":
                    yield emit(T_MODEQ, "%=")
                    i += 2
                    continue
                if ch == "&" and b == "=":
                    yield emit(T_ANDEQ, "&=")
                    i += 2
                    continue
                if ch == "|" and b == "=":
                    yield emit(T_OREQ, "|=")
                    i += 2
                    continue
                if ch == "^" and b == "=":
                    yield emit(T_XOREQ, "^=")
                    i += 2
                    continue

            # 1-char punct / ops
            if ch == "{":
                yield emit(T_LBRACE, ch)
                i += 1
                continue
            if ch == "}":
                yield emit(T_RBRACE, ch)
                i += 1
                continue
            if ch == "(":
                yield emit(T_LPAREN, ch)
                i += 1
                continue
            if ch == ")":
                yield emit(T_RPAREN, ch)
                i += 1
                continue
            if ch == "[":
                yield emit(T_LBRACK, ch)
                i += 1
                continue
            if ch == "]":
                yield emit(T_RBRACK, ch)
                i += 1
                continue
            if ch == ",":
                yield emit(T_COMMA, ch)
                i += 1
                continue
            if ch == ":":
                yield emit(T_COLON, ch)
                i += 1
                continue
            if ch == ";":
                yield emit(T_SEMICOL, ch)
                i += 1
                continue
            if ch == "+":
                yield emit(T_PLUS, ch)
                i += 1
                continue
            if ch == "-":
                yield emit(T_MINUS, ch)
                i += 1
                continue
            if ch == "*":
                yield emit(T_TIMES, ch)
                i += 1
                continue
            if ch == "%":
                yield emit(T_MOD, ch)
                i += 1
                continue
            if ch == "&":
                yield emit(T_AMP, ch)
                i += 1
                continue
            if ch == "|":
                yield emit(T_BAR, ch)
                i += 1
                continue
            if ch == "^":
                yield emit(T_CARET, ch)
                i += 1
                continue
            if ch == "~":
                yield emit(T_TILDE, ch)
                i += 1
                continue
            if ch == "<":
                yield emit(T_LT, ch)
                i += 1
                continue
            if ch == ">":
                yield emit(T_GT, ch)
                i += 1
                continue
            if ch == "=":
                yield emit(T_EQ, ch)
                i += 1
                continue
            if ch == "?":
                yield emit(T_QUESTION, ch)
                i += 1
                continue
            if ch == ".":
                yield emit(T_DOT, ch)
                i += 1
                continue
            if ch == "!":
                yield emit(T_NOT, ch)
                i += 1
                continue

            raise SyntaxError(f"Unexpected character at {code[i:i+10]!r}")

        # no explicit EOF needed (parser uses bounds)
