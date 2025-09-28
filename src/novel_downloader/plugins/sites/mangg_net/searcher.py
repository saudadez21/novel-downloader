#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mangg_net.searcher
-------------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class ManggNetSearcher(BaseSearcher):
    site_name = "mangg_net"
    priority = 30
    BASE_URL = "https://www.mangg.net/"
    SEARCH_URL = "https://www.mangg.net/search.php"

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
        rows = doc.xpath(
            '//div[contains(@class,"col-12") and contains(@class,"col-md-6")]/dl'
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(row.xpath("./dt/a/@href")) or cls._first_str(
                row.xpath("./dd/h3/a/@href")
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = cls._url_to_id(href)
            book_url = cls._abs_url(href)

            cover_src = cls._first_str(row.xpath("./dt/a/img/@src"))
            cover_url = cls._abs_url(cover_src) if cover_src else ""

            title = cls._first_str(row.xpath("./dd/h3/a/text()"))

            author = cls._first_str(
                row.xpath(
                    './/dd[contains(@class,"book_other")][contains(normalize-space(.),"作者")]/span/text()'
                )
            )
            latest_chapter = cls._first_str(
                row.xpath(
                    './/dd[contains(@class,"book_other")][contains(normalize-space(.),"最新章节")]//a/text()'
                )
            )
            update_date = cls._first_str(
                row.xpath(
                    './/dd[contains(@class,"book_other")][contains(normalize-space(.),"更新时间")]/text()'
                ),
                replaces=[("更新时间：", "")],
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

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/id84814/" -> "id84814"
        return url.strip("/")
