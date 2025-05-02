#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.common_parser.main_parser
-------------------------------------------------------

This package provides parsing components for handling
Common pages.
"""

from typing import Any, Dict

from novel_downloader.config import ParserConfig, SiteRules

from ..base_parser import BaseParser
from .helper import HTMLExtractor


class CommonParser(BaseParser):
    """
    CommonParser extends BaseParser to support site-specific parsing rules.

    It accepts additional site information and site-specific rules during initialization
    """

    def __init__(self, config: ParserConfig, site: str, site_rule: SiteRules):
        """
        Initialize the parser with configuration, site name, and site-specific rules.

        :param config: ParserConfig object controlling parsing behavior.
        :param site: Name of the site this parser is targeting.
        :param site_rule: SiteRules object containing parsing rules for the site.
        """
        super().__init__(config)
        self._site = site
        self._site_rule = site_rule

    def parse_book_info(self, html_str: str) -> Dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        extractor = HTMLExtractor(html_str)
        rules = self._site_rule["book_info"]
        return extractor.extract_book_info(rules)

    def parse_chapter(self, html_str: str, chapter_id: str) -> Dict[str, Any]:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        extractor = HTMLExtractor(html_str)
        chapter_rules = self._site_rule["chapter"]

        # 必须有正文内容
        content_steps = chapter_rules.get("content")
        if not content_steps:
            raise ValueError(f"No chapter content steps defined for site: {self._site}")

        title_steps = chapter_rules.get("title")
        title = extractor.extract_field(title_steps["steps"]) if title_steps else ""
        content = extractor.extract_field(content_steps["steps"])
        if not content:
            return {}

        return {
            "id": chapter_id,
            "title": title or "Untitled",
            "content": content,
            "site": self._site,
        }

    @property
    def site(self) -> str:
        """Return the site name."""
        return self._site

    @property
    def site_rule(self) -> SiteRules:
        """Return the site-specific rules."""
        return self._site_rule
