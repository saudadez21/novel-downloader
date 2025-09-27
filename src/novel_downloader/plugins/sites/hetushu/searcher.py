#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hetushu.searcher
-----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class HetushuSearcher(BaseSearcher):
    site_name = "hetushu"
    priority = 5
    SEARCH_URL = "https://www.hetushu.com/search/"
    BASE_URL = "https://www.hetushu.com"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {"keyword": keyword}
        headers = {
            "Referer": "https://www.hetushu.com/",
        }
        try:
            async with cls._http_get(
                cls.SEARCH_URL, params=params, headers=headers
            ) as resp:
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
        rows = doc.xpath('//dl[@class="list" and @id="body"]/dd')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(row.xpath(".//h4/a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # "/book/7631/index.html" -> "7631"
            book_id = href.rstrip("/index.html").split("/")[-1]
            book_url = cls._abs_url(href)

            title = cls._first_str(row.xpath(".//h4/a/text()"))

            # Author from the adjacent <span>, strip "/" delimiters
            # e.x. " / 风行云亦行 / "
            author_raw = cls._first_str(row.xpath(".//h4/span/text()"))
            author = author_raw.strip("/").strip()

            cover_rel = cls._first_str(row.xpath(".//a/img/@src"))
            cover_url = cls._abs_url(cover_rel) if cover_rel else ""

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
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
