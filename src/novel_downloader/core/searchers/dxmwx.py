#!/usr/bin/env python3
"""
novel_downloader.core.searchers.dxmwx
-------------------------------------

"""

import logging
from urllib.parse import urljoin

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["dxmwx"],
)
class DxmwxSearcher(BaseSearcher):
    site_name = "dxmwx"
    priority = 30
    BASE_URL = "https://www.dxmwx.org"
    SEARCH_URL = "https://www.dxmwx.org/list/{query}.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Dxmwx's search page.

        :param keyword: The search term to query on Dxmwx.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        try:
            async with (await cls._http_get(url)) as resp:
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
        Parse raw HTML from Dxmwx search results into list of SearchResult.

        :param html_str: Raw HTML string from Dxmwx search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath(
            "//div[@id='ListContents']/div[contains(@style,'position: relative')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            title = cls._first_str(
                row.xpath(".//div[contains(@class,'margin0h5')]//a[1]/text()")
            )
            href = cls._first_str(
                row.xpath(".//div[contains(@class,'margin0h5')]//a[1]/@href")
            )
            book_url = cls._abs_url(href)
            book_id = cls._book_id_from_book_url(href)

            author = cls._first_str(
                row.xpath(".//div[contains(@class,'margin0h5')]//a[2]/text()")
            )

            cover_url = cls._abs_url(
                cls._first_str(
                    row.xpath(".//div[contains(@class,'imgwidth')]//img/@src")
                )
            )

            latest_a_nodes = row.xpath(
                ".//a[span and span[contains(normalize-space(.), '最新章节')]]"
            )
            latest_chapter = ""
            if latest_a_nodes:
                txt = latest_a_nodes[0].text_content()
                latest_chapter = txt.replace("最新章节", "").strip()

            update_date = cls._first_str(
                row.xpath(".//span[contains(@class,'lefth5')]/text()")
            )

            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count="-",
                    priority=prio,
                )
            )
        return results

    @staticmethod
    def _book_id_from_book_url(href: str) -> str:
        # "/book/10409.html" -> "10409"
        return href.split("/book/", 1)[-1].split(".html", 1)[0]

    @classmethod
    def _abs_url(cls, url: str) -> str:
        return (
            url
            if url.startswith(("http://", "https://"))
            else urljoin(cls.BASE_URL, url)
        )
