#!/usr/bin/env python3
"""
novel_downloader.plugins.common.searcher.sososhu
------------------------------------------------

"""

import logging
from typing import ClassVar

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


class SososhuSearcher(BaseSearcher):
    priority = 30

    site_name = "sososhu"
    SOSOSHU_KEY: ClassVar[str]
    BASE_URL: ClassVar[str]
    SEARCH_URL = "https://www.sososhu.com/"

    async def _fetch_html(self, keyword: str) -> str:
        params = {
            "q": keyword,
            "site": self.SOSOSHU_KEY,
        }
        try:
            async with self._http_get(self.SEARCH_URL, params=params) as resp:
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

            book_url = self._restore_url(self._abs_url(href))
            book_id = self._url_to_id(book_url)

            title = self._first_str(row.xpath(".//dl/dt/a[1]/text()"))
            author = self._first_str(row.xpath(".//dl/dt/span[1]/text()"))
            cover_url = self._first_str(
                row.xpath(".//div[contains(@class,'image')]//img/@src")
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results

    @staticmethod
    def _restore_url(url: str) -> str:
        return url

    @staticmethod
    def _url_to_id(url: str) -> str:
        return url
