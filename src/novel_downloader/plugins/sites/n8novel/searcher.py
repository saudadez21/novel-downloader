#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n8novel.searcher
-----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class N8novelSearcher(BaseSearcher):
    site_name = "n8novel"
    priority = 20
    BASE_URL = "https://www.8novel.com"
    SEARCH_URL = "https://www.8novel.com/search/"

    async def _fetch_html(self, keyword: str) -> str:
        params = {"key": keyword}
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
        anchors = doc.xpath("//div[contains(@class,'picsize')]/a")
        results: list[SearchResult] = []

        for idx, a in enumerate(anchors):
            href = self._first_str(a.xpath("./@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/novelbooks/6045' -> "6045"
            book_id = href.rstrip("/").split("/")[-1]
            book_url = self._abs_url(href)

            cover_rel = self._first_str(a.xpath(".//img/@src"))
            cover_url = self._abs_url(cover_rel) if cover_rel else ""

            title = self._first_str(a.xpath("./@title"))

            word_count = self._first_str(a.xpath(".//eps//text()")) or "-"

            # Compute priority
            prio = self.priority + idx

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author="-",
                    latest_chapter="-",
                    update_date="-",
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
