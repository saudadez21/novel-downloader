#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.esjzone.searcher
-----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class EsjzoneSearcher(BaseSearcher):
    site_name = "esjzone"
    priority = 30
    BASE_URL = "https://www.esjzone.cc"
    SEARCH_URL = "https://www.esjzone.cc/tags/{query}/"

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
                url,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        cards = doc.xpath('//div[contains(@class,"card-body")]')
        results: list[SearchResult] = []

        for idx, card in enumerate(cards):
            href = cls._first_str(
                card.xpath(".//h5[contains(@class,'card-title')]/a[1]/@href")
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # href format: /detail/<book_id>.html
            book_id = href.split("/")[-1].split(".")[0]
            book_url = cls._abs_url(href)

            title = cls._first_str(
                card.xpath(".//h5[contains(@class,'card-title')]/a[1]//text()")
            )

            latest_chapter = (
                cls._first_str(
                    card.xpath(".//div[contains(@class,'card-ep')]//a[1]//text()")
                )
                or "-"
            )

            # Author
            author = cls._first_str(
                card.xpath(".//div[contains(@class,'card-author')]//a[1]//text()")
            ) or cls._first_str(
                card.xpath(".//div[contains(@class,'card-author')]//text()")
            )

            cover_data = card.xpath(
                './preceding-sibling::a[contains(@class,"card-img-tiles")]'
                '//div[contains(@class,"lazyload")]/@data-src'
            )
            cover_url = cover_data[0].strip() if cover_data else ""

            # Compute priority incrementally
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
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
