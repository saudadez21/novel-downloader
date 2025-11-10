#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.czbooks.searcher
-----------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class CzbooksSearcher(BaseSearcher):
    site_name = "czbooks"
    priority = 500
    BASE_URL = "https://czbooks.net/"
    SEARCH_URL = "https://czbooks.net/s/{query}"

    @property
    def nsfw(self) -> bool:
        return True

    async def _fetch_html(self, keyword: str) -> str:
        url = self.SEARCH_URL.format(query=self._quote(keyword))
        params = {"q": keyword}
        try:
            async with self.session.get(url, params=params) as resp:
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
            "//ul[contains(@class,'novel-list')]//li[contains(@class,'novel-item-wrapper')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(
                row.xpath(
                    ".//div[contains(@class,'novel-item-cover-wrapper')]//a/@href"
                )
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_url = self._abs_url(href)
            # "//czbooks.net/n/c8idd3" -> "c8idd3"
            book_id = href.rsplit("/", 1)[-1]

            title = self._first_str(
                row.xpath(".//div[contains(@class,'novel-item-title')]/text()")
            )
            author = self._first_str(
                row.xpath(".//div[contains(@class,'novel-item-author')]//a/text()")
            )
            cover_url = self._first_str(
                row.xpath(".//div[contains(@class,'novel-item-thumbnail')]//img/@src")
            )
            cover_url = self._abs_url(cover_url) if cover_url else ""

            latest_chapter = self._first_str(
                row.xpath(
                    ".//div[contains(@class,'novel-item-newest-chapter')]//a/text()"
                )
            )
            update_date = self._first_str(
                row.xpath(".//div[contains(@class,'novel-item-date')]/text()")
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
                    update_date=update_date,
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        print(results)
        return results
