#!/usr/bin/env python3
"""
novel_downloader.libs.textutils.text_cleaner
--------------------------------------------

Provides utilities to clean novel titles and content
by removing unwanted patterns, replacing strings.
"""

import re
from re import Match, Pattern
from typing import Protocol, runtime_checkable

from novel_downloader.schemas import TextCleanerConfig


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
    """
    TextCleaner removes invisible characters, strips unwanted patterns,
    and applies literal replacements in a single pass using a combined regex.

    For regex that never matches (r"$^"), reference:

    https://stackoverflow.com/questions/2930182/regex-to-not-match-anything
    """

    _INVISIBLE_PATTERN: Pattern[str] = re.compile(r"[\ufeff\u200B\u200C\u200D\u2060]")

    def __init__(self, config: TextCleanerConfig) -> None:
        """
        Initialize TextCleaner with the given configuration.

        Configuration fields (from ``TextCleanerConfig``):
          * remove_invisible: whether to strip BOM/zero-width chars
          * title_remove_patterns: list of regex patterns to delete from titles
          * content_remove_patterns: list of regex patterns to delete from content
          * title_replacements: dict of literal replacements for titles
          * content_replacements: dict of literal replacements for content

        :param config: A ``TextCleanerConfig`` instance.
        """
        self._remove_invisible = config.remove_invisible

        # Build literal‐to‐literal replacement maps
        self._title_repl_map = config.title_replacements
        self._content_repl_map = config.content_replacements

        # Deduplicate removal patterns (keep order)
        title_remove = list(dict.fromkeys(config.title_remove_patterns))
        content_remove = list(dict.fromkeys(config.content_remove_patterns))

        # Build a single combined regex for title:
        #   all delete‐patterns OR all escaped replacement‐keys
        self._title_combined_rx: re.Pattern[str] | None = None
        if title_remove or self._title_repl_map:
            title_parts = title_remove + [re.escape(k) for k in self._title_repl_map]
            # longer first to avoid prefix collisions
            title_parts.sort(key=len, reverse=True)
            self._title_combined_rx = re.compile("|".join(title_parts))

        # Build a single combined regex for content (multiline mode)
        self._content_combined_rx: re.Pattern[str] | None = None
        if content_remove or self._content_repl_map:
            content_parts = content_remove + [
                re.escape(k) for k in self._content_repl_map
            ]
            content_parts.sort(key=len, reverse=True)
            self._content_combined_rx = re.compile(
                "|".join(content_parts), flags=re.MULTILINE
            )

    def clean_title(self, text: str) -> str:
        """
        Clean a title string.

        Steps:
          1. Optionally strip BOM & zero-width characters.
          2. Remove unwanted patterns and apply literal replacements in one pass.
          3. Trim leading/trailing whitespace.

        :param text: Raw title text.
        :return: Cleaned title.
        """
        return self._do_clean(text, self._title_combined_rx, self._title_repl_map)

    def clean_content(self, text: str) -> str:
        """
        Clean a content string.

        Steps:
          1. Optionally strip BOM & zero-width characters.
          2. Remove unwanted patterns and apply literal replacements in one pass.
          3. Trim leading/trailing whitespace.

        :param text: Raw content/body text.
        :return: Cleaned content.
        """
        return self._do_clean(text, self._content_combined_rx, self._content_repl_map)

    def clean(self, text: str, *, as_title: bool = False) -> str:
        """
        Unified clean method to process text as either title or content.

        :param text: Raw text to clean.
        :param as_title: If True, use title rules; otherwise content rules.
        :return: Cleaned text.
        """
        return self.clean_title(text) if as_title else self.clean_content(text)

    @classmethod
    def _remove_bom_and_invisible(cls, text: str) -> str:
        """
        Remove BOM and zero-width/invisible characters from the text.

        Matches:
          * U+FEFF (BOM)
          * U+200B ZERO WIDTH SPACE
          * U+200C ZERO WIDTH NON-JOINER
          * U+200D ZERO WIDTH JOINER
          * U+2060 WORD JOINER

        :param text: Input string possibly containing invisible chars.
        :return: String with those characters stripped.
        """
        return cls._INVISIBLE_PATTERN.sub("", text)

    def _do_clean(
        self,
        text: str,
        combined_rx: Pattern[str] | None,
        repl_map: dict[str, str],
    ) -> str:
        """
        Core cleaning logic:
        optional invisible removal, single-pass remove/replace, trimming.

        :param text: Text to clean.
        :param combined_rx: Compiled regex for removal patterns and replacement keys.
        :param repl_map: Mapping from matched token to replacement text.
        :return: Cleaned text.
        """
        if not self._remove_invisible and not combined_rx:
            return text.strip()

        # Strip invisible chars if configured
        if self._remove_invisible:
            text = self._remove_bom_and_invisible(text)

        # Single‐pass removal & replacement
        if combined_rx:

            def _sub(match: Match[str]) -> str:
                # If token in repl_map -> replacement; else -> delete (empty string)
                return repl_map.get(match.group(0), "")

            text = combined_rx.sub(_sub, text)

        return text.strip()


def get_cleaner(
    enabled: bool,
    config: TextCleanerConfig,
) -> Cleaner:
    return TextCleaner(config) if enabled else NullCleaner()
