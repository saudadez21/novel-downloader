#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ixdzs8.searcher
----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class Ixdzs8Searcher(BaseSearcher):
    site_name = "ixdzs8"
    priority = 30
    BASE_URL = "https://ixdzs8.com"
    SEARCH_URL = "https://ixdzs8.com/bsearch"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {"q": keyword}
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
        rows = doc.xpath("//ul[contains(@class,'u-list')]/li[contains(@class,'burl')]")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            book_path = cls._first_str(row.xpath("./@data-url"))
            if not book_path:
                book_path = cls._first_str(
                    row.xpath(".//h3[contains(@class,'bname')]/a/@href")
                )
            if not book_path:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = book_path.strip("/").split("/")[-1]
            book_url = cls._abs_url(book_path)

            cover_rel = cls._first_str(
                row.xpath(".//div[contains(@class,'l-img')]//img/@src")
            )
            cover_url = cls._abs_url(cover_rel) if cover_rel else ""

            title = cls._first_str(
                row.xpath(".//h3[contains(@class,'bname')]/a/@title")
            ) or cls._first_str(row.xpath(".//h3[contains(@class,'bname')]/a/text()"))

            author = cls._first_str(
                row.xpath(".//span[contains(@class,'bauthor')]//a/text()")
            )
            word_count = cls._first_str(
                row.xpath(".//span[contains(@class,'size')]/text()")
            )

            latest_chapter = cls._first_str(
                row.xpath(
                    ".//p[contains(@class,'l-last')]//span[contains(@class,'l-chapter')]/text()"
                )
            )
            update_date = cls._first_str(
                row.xpath(
                    ".//p[contains(@class,'l-last')]//span[contains(@class,'l-time')]/text()"
                )
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
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
