#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n37yq.searcher
---------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class N37yqSearcher(BaseSearcher):
    site_name = "n37yq"
    priority = 10
    SEARCH_URL = "https://www.37yq.com/so.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        payload = {
            "searchkey": keyword,
            "searchtype": "all",
        }
        try:
            async with cls._http_post(cls.SEARCH_URL, data=payload) as resp:
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
            "//div[contains(@class,'search-tab')]//div[contains(@class,'search-result-list')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            book_url = cls._first_str(
                row.xpath(".//h2[contains(@class,'tit')]/a/@href")
                or row.xpath(".//div[contains(@class,'imgbox')]//a/@href")
            )
            if not book_url:
                continue

            if limit is not None and idx >= limit:
                break

            # 'https://www.37yq.com/lightnovel/3860.html' -> "3860"
            book_id = book_url.rsplit("/", 1)[-1].split(".")[0]

            cover_url = cls._first_str(
                row.xpath(".//div[contains(@class,'imgbox')]//img/@src")
            )
            title = cls._first_str(row.xpath(".//h2[contains(@class,'tit')]/a/text()"))
            author = cls._first_str(
                row.xpath(".//div[contains(@class,'bookinfo')]//a[1]/text()")
            )

            word_count = cls._first_str(
                row.xpath(".//div[contains(@class,'bookinfo')]//span//script/text()"),
                replaces=[("towan('", ""), ("')", "")],
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
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
