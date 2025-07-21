#!/usr/bin/env python3
"""
novel_downloader.core.searchers.qianbi
-----------------------------------------

"""

import logging
import re

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
        if html_str.find('<meta property="og:url"') != -1:
            return cls._parse_detail_html(html_str)
        return cls._parse_search_list_html(html_str, limit)

    @classmethod
    def _parse_detail_html(cls, html_str: str) -> list[SearchResult]:
        """
        Parse a single-book detail page, detected via <meta property="og:url">.

        :param html_str: Raw HTML of the book detail page.
        :return: A single-element list with the book's SearchResult.
        """
        doc = html.fromstring(html_str)
        url = doc.xpath('//meta[@property="og:url"]/@content')
        if not url:
            return []

        # extract book_id via regex
        m = re.search(r"/book/(\d+)/", url[0])
        book_id = m.group(1) if m else ""
        # title from <h1 class="page-title">
        title = (doc.xpath('//h1[@class="page-title"]/text()') or [""])[0].strip()
        author = (doc.xpath('//a[contains(@href,"/author/")]/@title') or [""])[
            0
        ].strip()

        return [
            SearchResult(
                site=cls.site_name,
                book_id=book_id,
                title=title,
                author=author,
                priority=cls.priority,
            )
        ]

    @classmethod
    def _parse_search_list_html(
        cls, html_str: str, limit: int | None
    ) -> list[SearchResult]:
        """
        Parse a multi-item search result page.

        :param html_str: Raw HTML of the search-results page.
        :param limit:    Maximum number of items to return, or None for all.
        :return:         List of SearchResult.
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
