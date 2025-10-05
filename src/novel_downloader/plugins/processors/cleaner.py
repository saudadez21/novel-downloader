#!/usr/bin/env python3
"""
novel_downloader.plugins.processors.cleaner
-------------------------------------------

A text cleaner that removes invisible characters, deletes unwanted patterns,
and applies literal replacements for both book-level metadata and chapters.
"""

from __future__ import annotations

import copy
import json
import re
from re import Match, Pattern
from typing import Any

from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import BookInfoDict, ChapterDict


@registrar.register_processor()
class CleanerProcessor:
    """
    Implements the Processor protocol to clean book and chapter data.
    """

    _INVISIBLE_PATTERN: Pattern[str] = re.compile(r"[\ufeff\u200B\u200C\u200D\u2060]")

    def __init__(self, config: dict[str, Any]) -> None:
        self._remove_invisible: bool = bool(config.get("remove_invisible", True))

        # --- load JSON files ---
        title_remove_patterns = self._load_str_list(
            str(config.get("title_removes") or "")
        )
        content_remove_patterns = self._load_str_list(
            str(config.get("content_removes") or "")
        )
        title_replacements = self._load_str_dict(str(config.get("title_replace") or ""))
        content_replacements = self._load_str_dict(
            str(config.get("content_replace") or "")
        )

        # dedupe removal patterns (preserve order)
        title_remove = list(dict.fromkeys(title_remove_patterns))
        content_remove = list(dict.fromkeys(content_remove_patterns))

        self._title_repl_map: dict[str, str] = title_replacements
        self._content_repl_map: dict[str, str] = content_replacements

        # build combined regexes (longer first to avoid prefix collisions)
        self._title_combined_rx: Pattern[str] | None = None
        if title_remove or self._title_repl_map:
            parts = title_remove + [re.escape(k) for k in self._title_repl_map]
            parts.sort(key=len, reverse=True)
            self._title_combined_rx = re.compile("|".join(parts))

        self._content_combined_rx: Pattern[str] | None = None
        if content_remove or self._content_repl_map:
            parts = content_remove + [re.escape(k) for k in self._content_repl_map]
            parts.sort(key=len, reverse=True)
            self._content_combined_rx = re.compile("|".join(parts), flags=re.MULTILINE)

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        """
        Apply cleaning rules to book metadata and nested structures.
        """
        bi = copy.deepcopy(book_info)

        if isinstance(name := bi.get("book_name"), str):
            bi["book_name"] = self._clean_title(name)
        if isinstance(author := bi.get("author"), str):
            bi["author"] = self._clean_title(author)

        if isinstance(summary := bi.get("summary"), str):
            bi["summary"] = self._clean_content(summary)

        if isinstance(tags := bi.get("tags"), list):
            bi["tags"] = [
                self._clean_title(t) if isinstance(t, str) else t for t in tags
            ]

        if isinstance(volumes := bi.get("volumes"), list):
            for vol in volumes:
                if isinstance(vname := vol.get("volume_name"), str):
                    vol["volume_name"] = self._clean_title(vname)

                if isinstance(intro := vol.get("volume_intro"), str):
                    vol["volume_intro"] = self._clean_content(intro)

                if isinstance(chapters := vol.get("chapters"), list):
                    for cinfo in chapters:
                        if isinstance(ctitle := cinfo.get("title"), str):
                            cinfo["title"] = self._clean_title(ctitle)

        return bi

    def process_chapter(self, chapter: ChapterDict) -> ChapterDict:
        """
        Apply cleaning rules to a single chapter (title + content).
        """
        ch = copy.deepcopy(chapter)

        if isinstance(title := ch.get("title"), str):
            ch["title"] = self._clean_title(title)
        if isinstance(content := ch.get("content"), str):
            ch["content"] = self._clean_content(content)

        return ch

    @classmethod
    def _remove_bom_and_invisible(cls, text: str) -> str:
        return cls._INVISIBLE_PATTERN.sub("", text)

    def _clean_title(self, text: str) -> str:
        return self._do_clean(text, self._title_combined_rx, self._title_repl_map)

    def _clean_content(self, text: str) -> str:
        return self._do_clean(text, self._content_combined_rx, self._content_repl_map)

    def _do_clean(
        self,
        text: str,
        combined_rx: Pattern[str] | None,
        repl_map: dict[str, str],
    ) -> str:
        if not isinstance(text, str):
            return text  # defensive

        if not self._remove_invisible and not combined_rx:
            return text.strip()

        if self._remove_invisible:
            text = self._remove_bom_and_invisible(text)

        if combined_rx:

            def _sub(match: Match[str]) -> str:
                return repl_map.get(match.group(0), "")

            text = combined_rx.sub(_sub, text)

        return text.strip()

    @staticmethod
    def _load_str_list(path: str) -> list[str]:
        """
        Load a JSON file containing a list of strings.
        Returns [] if path is empty/invalid/unreadable.
        """
        if not path:
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return list(data) if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def _load_str_dict(path: str) -> dict[str, str]:
        """
        Load a JSON file containing a dict of string-to-string mappings.
        Returns {} if path is empty/invalid/unreadable.
        """
        if not path:
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return (
                    {str(k): str(v) for k, v in data.items()}
                    if isinstance(data, dict)
                    else {}
                )
        except Exception:
            return {}
