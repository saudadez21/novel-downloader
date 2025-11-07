#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.fanqienovel.parser
-------------------------------------------------
"""

import json
import logging
import re
from typing import Any

from lxml import html
from novel_downloader.infra.paths import FANQIENOVEL_MAP_PATH
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class FanqienovelParser(BaseParser):
    """
    Parser for 番茄小说网 book pages.
    """

    site_name: str = "fanqienovel"

    _FONT_MAP: dict[str, str] = {}
    _RE_INT = re.compile(r"[+-]?\d+")
    _RE_FLOAT = re.compile(
        r"^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$|^[+-]?\d+[eE][+-]?\d+$"
    )
    _RE_INITIAL_STATE = re.compile(r"window\.__INITIAL_STATE__\s*=\s*({.*});", re.S)

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        data = self._extract_initial_state(html_list[0])
        page = data.get("page") or {}
        if not isinstance(page, dict):
            return None

        book_name = page.get("bookName") or ""
        author = page.get("authorName") or page.get("author") or ""
        cover_url = page.get("thumbUrl") or page.get("thumbUri") or ""
        update_time = page.get("lastPublishTime") or ""
        summary = page.get("abstract") or page.get("description") or ""

        tags: list[str] = []
        category_str = page.get("categoryV2")
        if isinstance(category_str, str):
            try:
                category_data = json.loads(category_str)
                tags = [c.get("Name", "") for c in category_data if c.get("Name")]
            except Exception:
                pass

        word_count = str(page.get("wordNumber") or "")
        serial_status = "完结" if page.get("creationStatus") == 2 else "连载"

        # --- Volumes and chapters ---
        volumes: list[VolumeInfoDict] = []
        volume_names: list[str] = page.get("volumeNameList") or []
        chapter_groups: list[list[dict[str, Any]]] = (
            page.get("chapterListWithVolume") or []
        )

        for i, chapter_list in enumerate(chapter_groups):
            if not isinstance(chapter_list, list):
                continue

            if i < len(volume_names):
                volume_name: str = str(volume_names[i])
            elif chapter_list:
                volume_name = str(chapter_list[0].get("volume_name") or f"卷 {i+1}")
            else:
                volume_name = f"卷 {i+1}"

            def _sort_key(ch_item: dict[str, Any]) -> Any:
                v = ch_item.get("realChapterOrder") or ch_item.get("itemId") or "0"
                try:
                    return int(v)
                except Exception:
                    return str(v or "")

            chapter_list.sort(key=_sort_key)

            chapters: list[ChapterInfoDict] = []
            for ch in chapter_list:
                chapter_id = str(ch.get("itemId") or "")
                title = ch.get("title") or ""
                accessible = not bool(ch.get("isChapterLock"))
                chapters.append(
                    {
                        "title": title,
                        "url": f"https://fanqienovel.com/reader/{chapter_id}",
                        "chapterId": chapter_id,
                        "accessible": accessible,
                    }
                )

            volumes.append(
                {
                    "volume_name": volume_name,
                    "chapters": chapters,
                }
            )

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
            "summary": summary,
            "tags": tags,
            "volumes": volumes,
            "extra": {
                "bookId": page.get("bookId"),
                "authorId": page.get("authorId"),
            },
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            return None

        html_str = html_list[0]
        self._check_font(html_str)

        data = self._extract_initial_state(html_str)
        chapter_data = self._extract_chapter_data(data)
        if not chapter_data:
            logger.warning(
                "fanqienovel: chapterData not found (chapter=%s)", chapter_id
            )
            return None

        raw_content = chapter_data.get("content")
        if not raw_content:
            logger.warning("fanqienovel: empty content (chapter=%s)", chapter_id)
            return None

        tree = html.fromstring(raw_content)
        paragraphs: list[str] = []
        for p in tree.xpath("//p"):
            text = self._apply_font_mapping(p.text_content()).strip()
            if text:
                paragraphs.append(text)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)
        title = chapter_data.get("title") or ""

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    @classmethod
    def _apply_font_mapping(cls, text: str) -> str:
        """
        Apply font mapping to the input text.
        """
        if not cls._FONT_MAP:
            cls._FONT_MAP = json.loads(FANQIENOVEL_MAP_PATH.read_text(encoding="utf-8"))
        return "".join(cls._FONT_MAP.get(ch, ch) for ch in text)

    @staticmethod
    def _parse_js_string(s: str) -> str:
        """
        Parse a JavaScript string literal (with escape sequences).

        :param s: The quoted JS string literal.
        :return: The unescaped Python string.
        :raises ValueError: If the string is not a valid JS literal.
        """
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
                out.append(esc)  # tolerate unknown escapes

        return "".join(out)

    @classmethod
    def _parse_js_token(cls, tok: str) -> Any:
        """
        Parse a single JavaScript token into its Python equivalent.

        :param tok: The token string.
        :return: The parsed Python value.
        """
        tok = tok.strip()
        match tok:
            case "null" | "undefined":
                return None
            case "true":
                return True
            case "false":
                return False
            case _ if cls._RE_INT.fullmatch(tok):
                return int(tok)
            case _ if cls._RE_FLOAT.fullmatch(tok):
                return float(tok)
            case _ if tok.startswith("'") and tok.endswith("'"):
                return cls._parse_js_string(tok)
            case _ if tok.startswith('"') and tok.endswith('"'):
                return cls._parse_js_string(tok)
            case _:
                return tok  # identifier or unknown symbol

    @staticmethod
    def _tokenize_object(src: str) -> list[str]:
        """
        Tokenize a JavaScript object/array literal string.

        :param src: The JS source snippet.
        :return: A list of token strings.
        """
        toks = []
        i, n = 0, len(src)
        while i < n:
            ch = src[i]

            # Skip whitespace
            if ch in " \t\r\n":
                i += 1
                continue

            # String literal
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

            # Comment
            if ch == "/" and i + 1 < n and src[i + 1] in "/*":
                if src[i + 1] == "/":  # single line
                    i += 2
                    while i < n and src[i] not in "\r\n":
                        i += 1
                else:  # block comment
                    i += 2
                    while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                        i += 1
                    i += 2
                continue

            # Punctuation
            if ch in "{}[]:,":
                toks.append(ch)
                i += 1
                continue

            # Identifier or number
            j = i
            while j < n and src[j] not in " \t\r\n{}[]:,":
                j += 1
            toks.append(src[i:j])
            i = j

        return toks

    @classmethod
    def _parse_js_value(cls, tokens: list[str], idx: int) -> tuple[Any, int]:
        """
        Recursively parse a JavaScript value from token list.

        :param tokens: The token list.
        :param idx: The starting index.
        :return: (parsed_value, next_index)
        """
        tok = tokens[idx]

        if tok == "{":
            obj = {}
            idx += 1
            while tokens[idx] != "}":
                key = tokens[idx]
                if key[0] in ('"', "'"):
                    key = cls._parse_js_string(key)
                idx += 1
                if tokens[idx] != ":":
                    raise ValueError(f"Expected :, got {tokens[idx]}")
                idx += 1
                val, idx = cls._parse_js_value(tokens, idx)
                obj[key] = val
                if tokens[idx] == ",":
                    idx += 1
            return obj, idx + 1

        if tok == "[":
            arr = []
            idx += 1
            while tokens[idx] != "]":
                val, idx = cls._parse_js_value(tokens, idx)
                arr.append(val)
                if tokens[idx] == ",":
                    idx += 1
            return arr, idx + 1

        return cls._parse_js_token(tok), idx + 1

    @classmethod
    def _extract_initial_state(cls, html_str: str) -> dict[str, Any]:
        """
        Extract and parse the JavaScript object assigned to `__INITIAL_STATE__`

        :param html_str: The HTML source containing the assignment.
        :return: A Python dictionary parsed from the JS object.
        :raises ValueError: If the pattern is not found or parsing fails.
        """
        match = cls._RE_INITIAL_STATE.search(html_str)
        if not match:
            raise ValueError("Could not find 'window.__INITIAL_STATE__' in the HTML.")

        try:
            obj_str = match.group(1)
            tokens = cls._tokenize_object(obj_str)
            result, _ = cls._parse_js_value(tokens, 0)
            if not isinstance(result, dict):
                raise ValueError("Parsed value is not an object.")
            return result
        except Exception as e:
            raise ValueError(f"Failed to parse JS object: {e}") from e

    @staticmethod
    def _extract_chapter_data(data: dict[str, Any]) -> dict[str, Any]:
        reader = data.get("reader", {})
        chapterData = reader.get("chapterData", {})
        return chapterData if isinstance(chapterData, dict) else {}

    @staticmethod
    def _check_font(html_str: str) -> None:
        if "dc027189e0ba4cd.woff" not in html_str:
            logger.warning(
                "fanqienovel font check: Did not etected 'dc027189e0ba4cd.woff'. "
                "This may cause the content to be incorrect. "
                "Please report this issue so the handler can be updated."
            )
