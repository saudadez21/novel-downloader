#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.dxmwx.searcher
---------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class DxmwxSearcher(BaseSearcher):
    site_name = "dxmwx"
    priority = 30
    BASE_URL = "https://www.dxmwx.org"
    SEARCH_URL = "https://www.dxmwx.org/list/{query}.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        try:
            async with cls._http_get(url) as resp:
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
            "//div[@id='ListContents']/div[contains(@style,'position: relative')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(
                row.xpath(".//div[contains(@class,'margin0h5')]//a[1]/@href")
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_url = cls._abs_url(href)
            # "/book/10409.html" -> "10409"
            book_id = href.split("/")[-1].split(".", 1)[0]

            title = cls._first_str(
                row.xpath(".//div[contains(@class,'margin0h5')]//a[1]/text()")
            )

            author = cls._first_str(
                row.xpath(".//div[contains(@class,'margin0h5')]//a[2]/text()")
            )

            cover_src = cls._first_str(
                row.xpath(".//div[contains(@class,'imgwidth')]//img/@src")
            )
            cover_url = cls._abs_url(cover_src) if cover_src else ""

            latest_chapter = cls._first_str(
                row.xpath(
                    ".//a[span and span[contains(normalize-space(.),'最新章节')]]"
                    "/span/following-sibling::text()[1]"
                )
            )

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
