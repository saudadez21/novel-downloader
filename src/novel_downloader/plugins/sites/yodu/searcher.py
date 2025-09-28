#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yodu.searcher
--------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class YoduSearcher(BaseSearcher):
    site_name = "yodu"
    priority = 15
    BASE_URL = "https://www.yodu.org/"
    SEARCH_URL = "https://www.yodu.org/sa"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        payload = {
            "searchkey": keyword,
            "searchtype": "all",
        }
        try:
            async with cls._http_post(cls.SEARCH_URL, data=payload) as resp:
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
        rows = doc.xpath('//ul[contains(@class,"ser-ret")]/li')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(
                row.xpath('.//a[contains(@class,"g_thumb")]/@href')
            ) or cls._first_str(row.xpath(".//h3//a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/book/17551/?for-search' -> "17551"
            path_after_book = href.split("/book/", 1)[-1] if "/book/" in href else ""
            book_id = path_after_book.split("/", 1)[0] if path_after_book else ""
            book_url = cls._abs_url(href)

            cover_url = cls._first_str(
                row.xpath('.//a[contains(@class,"g_thumb")]//img/@_src')
            ) or cls._first_str(row.xpath('.//a[contains(@class,"g_thumb")]//img/@src'))

            title = cls._first_str(row.xpath(".//h3//a/@title")) or cls._first_str(
                row.xpath(".//h3//a//text()")
            )
            author = cls._first_str(row.xpath(".//em//span[2]/text()"))
            latest_chapter = cls._first_str(
                row.xpath('.//p[contains(.,"最新章节")]//a/text()')
            )

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date="-",
                    word_count="-",
                    priority=cls.priority + idx,
                )
            )
        return results
