#!/usr/bin/env python3
"""
novel_downloader.core.searchers.hetushu
---------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["hetushu"],
)
class HetushuSearcher(BaseSearcher):
    site_name = "hetushu"
    priority = 5
    SEARCH_URL = "https://www.hetushu.com/search/"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Hetushu's search page.

        :param keyword: The search term to query on Hetushu.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"keyword": keyword}
        headers = {
            "Referer": "https://www.hetushu.com/",
        }
        try:
            response = cls._http_get(cls.SEARCH_URL, params=params, headers=headers)
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
        Parse raw HTML from Hetushu search results into list of SearchResult.

        :param html_str: Raw HTML string from Hetushu search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//dl[@class="list" and @id="body"]/dd')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            # Extract the href and derive book_id
            href = row.xpath(".//h4/a/@href")[0].strip()
            match = re.search(r"/book/(\d+)/", href)
            book_id = match.group(1) if match else ""

            # Title of the work
            title = row.xpath(".//h4/a/text()")[0].strip()

            # Author from the adjacent <span>, strip "/" delimiters
            author = row.xpath(".//h4/span/text()")[0].strip().strip("/").strip()
            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
