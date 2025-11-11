#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.alicesw.searcher
-----------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class AliceswSearcher(BaseSearcher):
    site_name = "alicesw"
    priority = 500
    BASE_URL = "http://www.alicesw.com/"
    SEARCH_URL = "https://www.alicesw.com/search.html"

    @property
    def nsfw(self) -> bool:
        return True

    async def _fetch_html(self, keyword: str) -> str:
        params = {"q": keyword, "f": "_all"}
        try:
            async with self.session.get(self.SEARCH_URL, params=params) as resp:
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
        rows = doc.xpath("//div[contains(@class, 'list-group-item')]")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath(".//h5/a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
            book_url = self._abs_url(href)
            title = self._join_strs(row.xpath(".//h5/a//text()"))
            author = self._first_str(
                row.xpath(".//p[contains(@class,'text-muted')]/a/text()")
            )
            update_date = self._first_str(
                row.xpath(
                    ".//p[contains(@class,'timedesc')]/text()[contains(., '更新时间')]"
                )
            )
            update_date = update_date.split("更新时间：", 1)[-1]

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date=update_date,
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results
