#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yodu.searcher
--------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class YoduSearcher(BaseSearcher):
    site_name = "yodu"
    priority = 15
    BASE_URL = "https://www.yodu.org/"
    SEARCH_URL = "https://www.yodu.org/sa"

    async def _fetch_html(self, keyword: str) -> str:
        payload = {
            "searchkey": keyword,
            "searchtype": "all",
        }
        try:
            async with self._http_post(self.SEARCH_URL, data=payload) as resp:
                resp.raise_for_status()
                return await self._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                self.SEARCH_URL,
            )
            return ""

    def _parse_html(
        self, html_str: str, limit: int | None = None
    ) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        rows = doc.xpath('//ul[contains(@class,"ser-ret")]/li')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(
                row.xpath('.//a[contains(@class,"g_thumb")]/@href')
            ) or self._first_str(row.xpath(".//h3//a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/book/17551/?for-search' -> "17551"
            path_after_book = href.split("/book/", 1)[-1] if "/book/" in href else ""
            book_id = path_after_book.split("/", 1)[0] if path_after_book else ""
            book_url = self._abs_url(href)

            cover_url = self._first_str(
                row.xpath('.//a[contains(@class,"g_thumb")]//img/@_src')
            ) or self._first_str(
                row.xpath('.//a[contains(@class,"g_thumb")]//img/@src')
            )

            title = self._first_str(row.xpath(".//h3//a/@title")) or self._first_str(
                row.xpath(".//h3//a//text()")
            )
            author = self._first_str(row.xpath(".//em//span[2]/text()"))
            latest_chapter = self._first_str(
                row.xpath('.//p[contains(.,"最新章节")]//a/text()')
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date="-",
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results
