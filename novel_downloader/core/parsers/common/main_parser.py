#!/usr/bin/env python3
"""
novel_downloader.core.parsers.common.main_parser
------------------------------------------------

This package provides parsing components for handling
Common pages.
"""

from typing import Any

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import (
    ChapterDict,
    ParserConfig,
    SiteRules,
)

# from .helper import HTMLExtractor


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

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return {}
        # extractor = HTMLExtractor(html_list[0])
        # rules = self._site_rule["book_info"]
        # return extractor.extract_book_info(rules)
        return {}

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None
        # extractor = HTMLExtractor(html_list[0])
        # chapter_rules = self._site_rule["chapter"]

        # # 必须有正文内容
        # content_steps = chapter_rules.get("content")
        # if not content_steps:
        #     raise ValueError(f"No chapter content steps for site: {self._site}")

        # title_steps = chapter_rules.get("title")
        # title = extractor.extract_field(title_steps["steps"]) if title_steps else ""
        # content = extractor.extract_field(content_steps["steps"])
        # if not content:
        #     return None

        # return {
        #     "id": chapter_id,
        #     "title": title or "Untitled",
        #     "content": content,
        #     "extra": {
        #         "site": self._site,
        #     },
        # }
        return None

    @property
    def site(self) -> str:
        """Return the site name."""
        return self._site

    @property
    def site_rule(self) -> SiteRules:
        """Return the site-specific rules."""
        return self._site_rule
