#!/usr/bin/env python3
"""
novel_downloader.core.searchers.qianbi
-----------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["qianbi"],
)
class QianbiSearcher(BaseSearcher):
    site_name = "qianbi"
    priority = 3
    SEARCH_URL = "https://www.23qb.com/search.html"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Qianbi's search page.

        :param keyword: The search term to query on Qianbi.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"searchkey": keyword}
        try:
            response = cls._http_get(cls.SEARCH_URL, params=params)
            return response.text
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                cls.SEARCH_URL,
                exc_info=True,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from Qianbi search results into list of SearchResult.

        :param html_str: Raw HTML string from Qianbi search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        items = doc.xpath('//div[contains(@class,"module-search-item")]')
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            if limit is not None and idx >= limit:
                break
            # Title and book_id
            link = item.xpath('.//div[@class="novel-info-header"]/h3/a')[0]
            title = link.text_content().strip()
            href = link.get("href", "").strip("/")
            book_id = href.replace("book/", "").strip("/")
            # Author is not present on the page
            author = ""
            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    title=title,
                    author=author,
                    priority=prio,
                )
            )
        return results
