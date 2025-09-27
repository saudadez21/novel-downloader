#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.laoyaoxs.searcher
------------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class LaoyaoxsSearcher(BaseSearcher):
    site_name = "laoyaoxs"
    priority = 20
    BASE_URL = "https://www.laoyaoxs.org/"
    SEARCH_URL = "https://www.laoyaoxs.org/search.php"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {"key": keyword}
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
        rows = doc.xpath('//div[contains(@class,"result")]//li')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = cls._first_str(
                row.xpath('.//a[contains(@class,"book_cov")]/@href')
            ) or cls._first_str(
                row.xpath('.//div[contains(@class,"book_inf")]//h3/a/@href')
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/info/7449.html' -> "7449"
            book_id = href.rsplit("/", 1)[-1].split(".")[0]
            book_url = cls._abs_url(href)

            cover_raw = cls._first_str(
                row.xpath('.//a[contains(@class,"book_cov")]//img/@data-original')
            ) or cls._first_str(
                row.xpath('.//a[contains(@class,"book_cov")]//img/@src')
            )
            if cover_raw.startswith("//"):
                cover_raw = "https:" + cover_raw
            cover_url = cls._abs_url(cover_raw) if cover_raw else ""

            title = cls._first_str(
                row.xpath('.//div[contains(@class,"book_inf")]//h3/a/@title')
            )
            author = cls._first_str(
                row.xpath(
                    './/p[contains(@class,"tags")]//span[contains(.,"作者")]//a/text()'
                )
            )
            latest_chapter = cls._first_str(
                row.xpath('.//p[./b[contains(normalize-space(.),"最近更新")]]//a/text()')
            )
            update_date = cls._first_str(
                row.xpath('.//div[contains(@class,"right")]//span/text()'),
                replaces=[("更新时间：", "")],
            )
            word_count = cls._first_str(
                row.xpath(
                    './/p[contains(@class,"tags")]//span[contains(.,"总字数")]/text()'
                ),
                replaces=[("总字数：", "")],
            )

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
                    priority=cls.priority + idx,
                )
            )
        return results
