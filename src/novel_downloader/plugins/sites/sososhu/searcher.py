#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.sososhu.searcher
-----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


class SososhuSearcher(BaseSearcher):
    priority = 30

    site_name: str = "sososhu"
    SOSOSHU_KEY: str
    BASE_URL: str
    SEARCH_URL = "https://www.sososhu.com/"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {
            "q": keyword,
            "site": cls.SOSOSHU_KEY,
        }
        try:
            async with cls._http_get(cls.SEARCH_URL, params=params) as resp:
                resp.raise_for_status()
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
        doc = html.fromstring(html_str)
        rows = doc.xpath(
            "//div[contains(@class,'so_list')]//div[contains(@class,'hot')]//div[contains(@class,'item')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = next(iter(row.xpath(".//dl/dt/a[1]/@href")), "")
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_url = cls._restore_url(cls._abs_url(href))
            book_id = cls._url_to_id(book_url)

            title = cls._first_str(row.xpath(".//dl/dt/a[1]/text()"))
            author = cls._first_str(row.xpath(".//dl/dt/span[1]/text()"))
            cover_url = cls._first_str(
                row.xpath(".//div[contains(@class,'image')]//img/@src")
            )

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=cls.priority + idx,
                )
            )
        return results

    @staticmethod
    def _restore_url(url: str) -> str:
        return url

    @staticmethod
    def _url_to_id(url: str) -> str:
        return url
