#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ttkan.searcher
---------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class TtkanSearcher(BaseSearcher):
    site_name = "ttkan"
    priority = 100
    BASE_URL = "https://www.ttkan.co"
    SEARCH_URL = "https://www.ttkan.co/novel/search"

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
        items = doc.xpath(
            '//div[contains(@class,"frame_body")]//div[@class="pure-g"]/div[contains(@class,"novel_cell")]'
        )
        if not items:
            items = doc.xpath('//div[contains(@class,"novel_cell")]')
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            href = cls._first_str(item.xpath(".//a[@href][1]/@href"))
            if not href:
                continue

            if limit is not None and len(results) >= limit:
                break

            # link -> /novel/chapters/<book_id>
            book_id = href.strip("/").split("/")[-1]
            book_url = cls._abs_url(href)

            cover_rel = cls._first_str(item.xpath(".//amp-img/@src"))
            cover_url = cls._abs_url(cover_rel) if cover_rel else ""

            title = cls._first_str(item.xpath(".//h3/text()"))

            author = (
                cls._first_str(
                    item.xpath(".//li[starts-with(normalize-space(.),'作者')]/text()"),
                    replaces=[("作者：", "")],
                )
                or "-"
            )

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
