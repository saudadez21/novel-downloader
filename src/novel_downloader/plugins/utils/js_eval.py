#!/usr/bin/env python3
"""
novel_downloader.libs.js_eval
-----------------------------

Unified JS -> JSON evaluator with fast-path IIFE parsing.

Strategy:
  1) If input looks like a simple IIFE returning an object literal,
     parse it directly in Python (no subprocess).
  2) Otherwise or on parse failure, fallback to Node.js evaluator.
"""

from __future__ import annotations

__all__ = ["JsEvaluator"]

import json
import logging
import re
import shutil
import subprocess
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any

from novel_downloader.infra.paths import EXPR_TO_JSON_SCRIPT_PATH

logger = logging.getLogger(__name__)

_IIFE_RE = re.compile(
    r"^\(function\((.*?)\)\s*\{\s*return\s*({.*?})\s*\}\s*\((.*?)\)\)$",
    re.S,
)

_INT_RE = re.compile(r"[+-]?\d+")
_FLOAT_RE = re.compile(
    r"^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$|^[+-]?\d+[eE][+-]?\d+$"
)


def _parse_js_string(s: str) -> str:
    if not (s and s[0] == s[-1] and s[0] in ("'", '"')):
        raise ValueError(f"Invalid JS string literal: {s!r}")

    body = s[1:-1]
    if "\\" not in body:
        return body

    out = []
    it = iter(body)
    for ch in it:
        if ch != "\\":
            out.append(ch)
            continue

        try:
            esc = next(it)
        except StopIteration:
            break

        if esc in "'\"\\":
            out.append(esc)
        elif esc == "n":
            out.append("\n")
        elif esc == "r":
            out.append("\r")
        elif esc == "t":
            out.append("\t")
        elif esc == "b":
            out.append("\b")
        elif esc == "f":
            out.append("\f")
        elif esc == "v":
            out.append("\v")
        elif esc == "0":
            out.append("\0")
        elif esc == "x":
            hex2 = "".join(next(it) for _ in range(2))
            out.append(chr(int(hex2, 16)))
        elif esc == "u":
            hex4 = "".join(next(it) for _ in range(4))
            out.append(chr(int(hex4, 16)))
        else:
            out.append(esc)  # 宽松处理未知转义

    return "".join(out)


def _parse_js_token(tok: str) -> Any:
    tok = tok.strip()
    match tok:
        case "null" | "undefined":
            return None
        case "true":
            return True
        case "false":
            return False
        case _ if _INT_RE.fullmatch(tok):
            return int(tok)
        case _ if _FLOAT_RE.fullmatch(tok):
            return float(tok)
        case _ if tok.startswith("'") and tok.endswith("'"):
            return _parse_js_string(tok)
        case _ if tok.startswith('"') and tok.endswith('"'):
            return _parse_js_string(tok)
        case _:
            return tok  # 标识符等


def _split_args(s: str) -> list[str]:
    out = []
    buf = []
    stack = []

    it = iter(s)
    in_str = False
    esc = False
    quote = ""

    for ch in it:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue

        if ch in ('"', "'"):
            in_str = True
            quote = ch
            buf.append(ch)
            continue

        if ch in "{[(":
            stack.append(ch)
            buf.append(ch)
            continue

        if ch in "}])":
            if stack:
                stack.pop()
            buf.append(ch)
            continue

        if ch == "," and not stack:
            item = "".join(buf).strip()
            if item:
                out.append(item)
            buf.clear()
            continue

        buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        out.append(tail)

    return out


def _tokenize_object(src: str) -> list[str]:
    toks = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]

        # skip space
        if ch in " \t\r\n":
            i += 1
            continue

        # string
        if ch in ("'", '"'):
            quote = ch
            j = i + 1
            esc = False
            while j < n:
                c = src[j]
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == quote:
                    j += 1
                    break
                j += 1
            toks.append(src[i:j])
            i = j
            continue

        # comment
        if ch == "/" and i + 1 < n and src[i + 1] in "/*":
            if src[i + 1] == "/":
                i += 2
                while i < n and src[i] not in "\r\n":
                    i += 1
            else:
                i += 2
                while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                    i += 1
                i += 2
            continue

        # punctuation
        if ch in "{}[]:,":
            toks.append(ch)
            i += 1
            continue

        # identifier / number
        j = i
        while j < n and src[j] not in " \t\r\n{}[]:,":
            j += 1
        toks.append(src[i:j])
        i = j

    return toks


def _parse_js_value(
    tokens: list[str], idx: int, mapping: dict[str, Any]
) -> tuple[Any, int]:
    tok = tokens[idx]

    if tok == "{":
        obj = {}
        idx += 1
        while tokens[idx] != "}":
            key = tokens[idx]
            if key[0] in ('"', "'"):
                key = _parse_js_string(key)
            idx += 1
            if tokens[idx] != ":":
                raise ValueError(f"Expected :, got {tokens[idx]}")
            idx += 1
            val, idx = _parse_js_value(tokens, idx, mapping)
            obj[key] = val
            if tokens[idx] == ",":
                idx += 1
        return obj, idx + 1

    if tok == "[":
        arr = []
        idx += 1
        while tokens[idx] != "]":
            val, idx = _parse_js_value(tokens, idx, mapping)
            arr.append(val)
            if tokens[idx] == ",":
                idx += 1
        return arr, idx + 1

    if tok in mapping:
        return mapping[tok], idx + 1

    return _parse_js_token(tok), idx + 1


class JsEvaluator:
    """
    Unified evaluator:
      * fast direct IIFE parse
      * Node fallback for everything else
    """

    __slots__ = ("script_dir", "script_src", "node_bin", "script_name", "has_node")

    def __init__(
        self,
        script_dir: Path,
        script_src: Traversable | Path = EXPR_TO_JSON_SCRIPT_PATH,
        node_bin: str = "node",
        script_name: str = "expr_to_json.js",
    ) -> None:
        self.script_dir = script_dir
        self.script_src = script_src
        self.node_bin = node_bin
        self.script_name = script_name
        self.has_node = shutil.which(node_bin) is not None

    def eval(self, js_code: str) -> Any | None:
        if not js_code:
            logger.debug("JsEvaluator.eval: empty input.")
            return None

        s = js_code.strip()
        try:
            return self._eval_direct(s)
        except Exception as exc:
            logger.debug("Direct IIFE parse failed, falling back to Node: %s", exc)

        return self._eval_node(js_code)

    @staticmethod
    def _eval_direct(iife: str) -> Any:
        """
        Parse very specific IIFE shape:
          (function(a,b){ return { ... } }(1,"x"))

        :raise: ValueError if format doesn't match.
        """
        m = _IIFE_RE.match(iife.strip())
        if not m:
            raise ValueError("Invalid IIFE format")

        params_str, obj_str, args_str = m.groups()

        params = [p.strip() for p in _split_args(params_str)]
        args = [a.strip() for a in _split_args(args_str)]

        if len(params) != len(args):
            raise ValueError("Param/arg length mismatch")

        mapping = {p: _parse_js_token(a) for p, a in zip(params, args, strict=False)}

        tokens = _tokenize_object(obj_str)
        result, _ = _parse_js_value(tokens, 0, mapping)
        return result

    def _eval_node(self, js_code: str) -> Any | None:
        """Evaluate JS via Node only."""
        if not self.has_node:
            logger.info("Node evaluation skipped: Node.js not available.")
            return None

        proc = self._run_node(js_code)

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            raise RuntimeError(
                f"Node evaluation failed: {stderr or 'non-zero exit code'}"
            )

        stdout = (proc.stdout or "").strip()
        if not stdout:
            return {}

        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON from Node evaluator: %s", stdout)
            raise RuntimeError("Node evaluator produced invalid JSON.") from exc

    def _run_node(self, js_code: str) -> subprocess.CompletedProcess[str]:
        dst = self.script_dir / self.script_name
        if not dst.exists():
            self.script_dir.mkdir(parents=True, exist_ok=True)
            data = self.script_src.read_bytes()
            dst.write_bytes(data)

        return subprocess.run(
            [self.node_bin, str(dst)],
            input=js_code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.script_dir,
        )
