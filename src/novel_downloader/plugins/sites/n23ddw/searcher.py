#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23ddw.searcher
----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class N23ddwSearcher(BaseSearcher):
    site_name = "n23ddw"
    priority = 30
    BASE_URL = "https://www.23ddw.net/"
    SEARCH_URL = "https://www.23ddw.net/searchss/"

    async def _fetch_html(self, keyword: str) -> str:
        params = {"searchkey": keyword}
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
        rows = doc.xpath('//div[@id="hotcontent"]//div[@class="item"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath(".//dl/dt/a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # "/du/291/291325/" -> "291-291325"
            book_id = href.replace("/du/", "").strip("/").replace("/", "-")
            book_url = self._abs_url(href)

            title = self._first_str(row.xpath(".//dl/dt/a/text()"))
            author = self._first_str(
                row.xpath('.//div[contains(@class,"btm")]//a[1]/text()')
            )
            cover_url = self._first_str(
                row.xpath(
                    './/div[contains(@class,"image")]//img[1]/@data-original | '
                    './/div[contains(@class,"image")]//img[1]/@src'
                )
            )
            cover_url = self._abs_url(cover_url) if cover_url else ""

            word_count = (
                self._first_str(
                    row.xpath(
                        './/div[contains(@class,"btm")]//em[contains(@class,"orange")]/text()'
                    )
                )
                or "-"
            )
            update_date = (
                self._first_str(
                    row.xpath(
                        './/div[contains(@class,"btm")]//em[contains(@class,"blue")]/text()'
                    )
                )
                or "-"
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
                    update_date=update_date,
                    word_count=word_count,
                    priority=self.priority + idx,
                )
            )
        return results
