#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xiguashuwu.searcher
--------------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class XiguashuwuSearcher(BaseSearcher):
    site_name = "xiguashuwu"
    priority = 500
    BASE_URL = "https://www.xiguashuwu.com"
    SEARCH_URL = "https://www.xiguashuwu.com/search/{query}"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        headers = {
            "Referer": "https://www.xiguashuwu.com/search/",
        }
        try:
            async with cls._http_get(url, headers=headers) as resp:
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
        rows = doc.xpath('//div[@class="SHsectionThree-middle"]/p')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(
                row.xpath(".//a[starts-with(@href,'/book/')][1]/@href")
            ) or cls._first_str(row.xpath(".//a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/book/184974/iszip/0/' -> "184974"
            book_id = href.split("/book/")[-1].split("/")[0]
            book_url = cls._abs_url(href)

            title = (
                cls._first_str(
                    row.xpath(".//a[starts-with(@href,'/book/')][1]//text()")
                )
                or cls._first_str(row.xpath(".//a[1]//text()"))
                or "-"
            )

            author = (
                cls._first_str(
                    row.xpath(".//a[starts-with(@href,'/writer/')][1]//text()")
                )
                or cls._first_str(row.xpath(".//a[2]//text()"))
                or "-"
            )

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="-",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=cls.priority + idx,
                )
            )
        return results
