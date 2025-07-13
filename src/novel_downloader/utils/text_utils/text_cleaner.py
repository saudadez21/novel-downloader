#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.text_cleaner
----------------------------------------------

Provides utilities to clean novel titles and content
by removing unwanted patterns, replacing strings.
"""

import re

from novel_downloader.models import TextCleanerConfig


class TextCleaner:
    _INVISIBLE_PATTERN = re.compile(r"[\ufeff\u200B\u200C\u200D\u2060]")

    def __init__(self, config: TextCleanerConfig) -> None:
        self._cfg = config
        self._remove_invisible = config.remove_invisible

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
        if self._remove_invisible:
            text = self._remove_bom_and_invisible(text)
        for regex in self._cfg.title_remove_patterns:
            text = regex.sub("", text)
        for src, tgt in self._cfg.title_replacements.items():
            text = text.replace(src, tgt)
        return text.strip()

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
        if self._remove_invisible:
            text = self._remove_bom_and_invisible(text)
        for regex in self._cfg.content_remove_patterns:
            text = regex.sub("", text)
        for src, tgt in self._cfg.content_replacements.items():
            text = text.replace(src, tgt)
        return text.strip()

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
