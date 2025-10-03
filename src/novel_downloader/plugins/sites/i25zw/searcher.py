#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.i25zw.searcher
---------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class I25zwSearcher(BaseSearcher):
    site_name = "i25zw"
    priority = 30
    SEARCH_URL = "https://www.i25zw.com/search.html"

    async def _fetch_html(self, keyword: str) -> str:
        payload = {
            "searchkey": keyword,
            "searchtype": "all",
            "Submit": "",
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
        rows = doc.xpath("//div[@id='alistbox']")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            book_url = self._first_str(row.xpath(".//div[@class='pic']/a/@href"))
            if not book_url:
                continue

            if limit is not None and idx >= limit:
                break

            # 'https://www.i25zw.com/book/309209.html' -> "309209"
            book_id = book_url.split("/")[-1].split(".")[0]

            title = self._first_str(row.xpath(".//div[@class='title']/h2/a/text()"))

            author = self._first_str(
                row.xpath(".//div[@class='title']/span/text()"),
                replaces=[("作者：", "")],
            )

            cover_rel = self._first_str(row.xpath(".//div[@class='pic']//img/@src"))
            cover_url = self._abs_url(cover_rel) if cover_rel else ""

            # Latest chapter
            latest_chapter = (
                self._first_str(row.xpath(".//div[@class='sys']//li[1]/a/text()"))
                or "-"
            )

            prio = self.priority + idx

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
                    priority=prio,
                )
            )
        return results
