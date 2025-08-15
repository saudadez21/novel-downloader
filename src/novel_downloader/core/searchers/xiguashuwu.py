#!/usr/bin/env python3
"""
novel_downloader.core.searchers.xiguashuwu
--------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["xiguashuwu"],
)
class XiguashuwuSearcher(BaseSearcher):
    site_name = "xiguashuwu"
    priority = 500
    BASE_URL = "https://www.xiguashuwu.com"
    SEARCH_URL = "https://www.xiguashuwu.com/search/{query}"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Xiguashuwu's search page.

        :param keyword: The search term to query on Xiguashuwu.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        headers = {
            "Referer": "https://www.xiguashuwu.com/search/",
        }
        try:
            async with (await cls._http_get(url, headers=headers)) as resp:
                return await cls._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                cls.SEARCH_URL,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from Xiguashuwu search results into list of SearchResult.

        :param html_str: Raw HTML string from Xiguashuwu search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//div[@class="SHsectionThree-middle"]/p')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            # Book link: /book/{book_id}/...
            book_link = row.xpath(".//a[1]/@href")
            if not book_link:
                continue
            # Extract numeric book_id from URL
            m = re.search(r"/book/(\d+)/", book_link[0])
            if not m:
                continue
            book_id = m.group(1)
            book_url = cls.BASE_URL + book_link[0]

            # Title text
            title = row.xpath(".//a[1]/text()")
            title = title[0].strip() if title else "-"

            # Author text (second <a>)
            author = row.xpath(".//a[2]/text()")
            author = author[0].strip() if author else "-"

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="-",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=cls.priority + idx,
                )
            )
        return results
