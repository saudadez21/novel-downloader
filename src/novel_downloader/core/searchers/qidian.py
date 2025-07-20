#!/usr/bin/env python3
"""
novel_downloader.core.searchers.qidian
--------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["qidian", "qd"],
)
class QidianSearcher(BaseSearcher):
    site_name = "qidian"
    priority = 0
    SEARCH_URL = "https://www.qidian.com/so/{query}.html"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Qidian's search page.

        :param keyword: The search term to query on Qidian.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        try:
            response = cls._http_get(url)
            return response.text
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                url,
                exc_info=True,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from Qidian search results into list of SearchResult.

        :param html: Raw HTML string from Qidian search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        items = doc.xpath(
            '//div[@id="result-list"]//li[contains(@class, "res-book-item")]'
        )
        results: list[SearchResult] = []

        base_prio = getattr(cls, "priority", 0)
        for idx, item in enumerate(items):
            if limit is not None and idx >= limit:
                break
            book_id = item.get("data-bid")
            title_elem = item.xpath('.//h3[@class="book-info-title"]/a')[0]
            title = title_elem.text_content().strip()
            author_nodes = item.xpath(
                './/p[@class="author"]/a[@class="name"] | .//p[@class="author"]/i'
            )
            author = author_nodes[0].text_content().strip() if author_nodes else ""
            prio = base_prio + idx
            results.append(
                {
                    "site": cls.site_name,
                    "book_id": book_id,
                    "title": title,
                    "author": author,
                    "priority": prio,
                }
            )
        return results
