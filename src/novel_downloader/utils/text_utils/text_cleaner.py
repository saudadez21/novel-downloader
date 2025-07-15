#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.text_cleaner
----------------------------------------------

Provides utilities to clean novel titles and content
by removing unwanted patterns, replacing strings.
"""

import re
from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from novel_downloader.models import TextCleanerConfig


@runtime_checkable
class Cleaner(Protocol):
    def clean(self, text: str, *, as_title: bool = False) -> str:
        ...

    def clean_title(self, text: str) -> str:
        ...

    def clean_content(self, text: str) -> str:
        ...


class NullCleaner(Cleaner):
    def clean_title(self, text: str) -> str:
        return text

    def clean_content(self, text: str) -> str:
        return text

    def clean(self, text: str, *, as_title: bool = False) -> str:
        return text


class TextCleaner(Cleaner):
    _INVISIBLE_PATTERN = re.compile(r"[\ufeff\u200B\u200C\u200D\u2060]")

    def __init__(self, config: TextCleanerConfig) -> None:
        self._remove_invisible = config.remove_invisible
        self._title_remove = self._merge_patterns(
            config.title_remove_patterns,
        )
        self._content_remove = self._merge_patterns(
            config.content_remove_patterns,
            flags=re.MULTILINE,
        )
        self._title_replacements: list[tuple[str, str]] = sorted(
            config.title_replacements.items(),
            key=lambda kv: -len(kv[0]),
        )
        self._content_replacements: list[tuple[str, str]] = sorted(
            config.content_replacements.items(),
            key=lambda kv: -len(kv[0]),
        )

    def clean_title(self, text: str) -> str:
        """
        Clean a title string.

        Steps:
          1. Optionally strip BOM & zero-width characters.
          2. Remove all patterns in title_remove_patterns.
          3. Apply literal replacements from title_replacements.
          4. Trim leading/trailing whitespace.

        :param text: Raw title text.
        :return: Cleaned title.
        """
        return self._do_clean(
            text,
            self._title_remove,
            self._title_replacements,
            self._remove_invisible,
        )

    def clean_content(self, text: str) -> str:
        """
        Clean a content string.

        Steps:
          1. Optionally strip BOM & zero-width characters.
          2. Remove all patterns in content_remove_patterns.
          3. Apply literal replacements from content_replacements.
          4. Trim leading/trailing whitespace.

        :param text: Raw content/body text.
        :return: Cleaned content.
        """
        return self._do_clean(
            text,
            self._content_remove,
            self._content_replacements,
            self._remove_invisible,
        )

    def clean(self, text: str, *, as_title: bool = False) -> str:
        """
        Single-entry point to clean text as either title or content.

        :param text: The raw text.
        :param as_title: If True, use title rules; otherwise content rules.
        :return: The cleaned text.
        """
        if as_title:
            return self.clean_title(text)
        return self.clean_content(text)

    @classmethod
    def _remove_bom_and_invisible(cls, text: str) -> str:
        """
        Remove BOM and common zero-width/invisible characters from text.

        Matches:
          - U+FEFF (BOM)
          - U+200B ZERO WIDTH SPACE
          - U+200C ZERO WIDTH NON-JOINER
          - U+200D ZERO WIDTH JOINER
          - U+2060 WORD JOINER

        :param text: Input string possibly containing invisible chars.
        :return: String with those characters stripped.
        """
        return cls._INVISIBLE_PATTERN.sub("", text)

    @staticmethod
    def _merge_patterns(
        patterns: Iterable[str],
        flags: int = 0,
    ) -> re.Pattern[str]:
        """
        Merge a collection of regex pattern strings into a single compiled pattern.

        It sort the unique patterns by length in descending order, so that
        longer (more specific) patterns are attempted before shorter ones,
        preventing partial matches from shadowing full matches.

        If no patterns remain, return a regex that never matches (see ref).

        Reference:

        https://stackoverflow.com/questions/2930182/regex-to-not-match-anything

        :param patterns: An iterable of regex pattern strings.
        :return: A compiled `re.Pattern` matching any of the input patterns
        """
        unique_patterns = set(patterns)
        sorted_patterns = sorted(unique_patterns, key=len, reverse=True)
        if not sorted_patterns:
            return re.compile(r"$-")
        return re.compile(r"(?:{})".format("|".join(sorted_patterns)), flags=flags)

    @classmethod
    def _do_clean(
        cls,
        text: str,
        remove_rx: re.Pattern[str],
        replacements: Iterable[tuple[str, str]],
        remove_invisible: bool,
    ) -> str:
        if remove_invisible:
            text = cls._remove_bom_and_invisible(text)
        text = remove_rx.sub("", text)
        for src, tgt in replacements:
            text = text.replace(src, tgt)
        return text.strip()


def get_cleaner(
    enabled: bool,
    config: TextCleanerConfig,
) -> Cleaner:
    return TextCleaner(config) if enabled else NullCleaner()
