#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23qb.searcher
---------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.searching import register_searcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@register_searcher()
class N23qbSearcher(BaseSearcher):
    site_name = "n23qb"
    priority = 10
    BASE_URL = "https://www.23qb.com/"
    SEARCH_URL = "https://www.23qb.com/search.html"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        params = {"searchkey": keyword}
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
        if html_str.find('<meta property="og:url"') != -1:
            return cls._parse_detail_html(html_str)
        return cls._parse_search_list_html(html_str, limit)

    @classmethod
    def _parse_detail_html(cls, html_str: str) -> list[SearchResult]:
        """
        Parse a single-book detail page, detected via <meta property="og:url">.

        :param html_str: Raw HTML of the book detail page.
        :return: A single-element list with the book's SearchResult.
        """
        doc = html.fromstring(html_str)

        book_url = cls._first_str(doc.xpath("//meta[@property='og:url']/@content"))
        if not book_url:
            return []

        # 'https://www.23qb.com/book/9268/' -> "9268"
        book_id = book_url.split("book/", 1)[-1].strip("/")

        cover_rel = cls._first_str(
            doc.xpath("//div[contains(@class,'novel-cover')]//img/@data-src")
        ) or cls._first_str(
            doc.xpath("//div[contains(@class,'novel-cover')]//img/@src")
        )
        cover_url = cls._abs_url(cover_rel) if cover_rel else ""

        title = cls._first_str(doc.xpath("//h1[@class='page-title']/text()"))
        author = cls._first_str(doc.xpath("//a[contains(@href, '/author/')]/@title"))

        latest_chapter = (
            cls._first_str(
                doc.xpath(
                    "//div[@class='module-row-info']//a[@class='module-row-text']/@title"
                )
            )
            or "-"
        )
        update_date = (
            cls._first_str(
                doc.xpath("//div[@class='module-heading newchapter']/time/text()"),
                replaces=[("更新时间：", "")],
            )
            or "-"
        )

        word_count = cls._first_str(doc.xpath("//span[contains(text(), '字')]/text()"))

        return [
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
                priority=cls.priority,
            )
        ]

    @classmethod
    def _parse_search_list_html(
        cls, html_str: str, limit: int | None
    ) -> list[SearchResult]:
        """
        Parse a multi-item search result page.

        :param html_str: Raw HTML of the search-results page.
        :param limit: Maximum number of items to return, or None for all.
        :return: List of SearchResult.
        """
        doc = html.fromstring(html_str)
        items = doc.xpath('//div[contains(@class,"module-search-item")]')
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            href = cls._first_str(
                item.xpath(".//div[@class='novel-info-header']/h3/a/@href")
            )
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/book/9138/' -> "9138"
            book_id = href.rstrip("/").split("/")[-1]
            book_url = cls._abs_url(href)

            title = cls._first_str(
                item.xpath(".//div[@class='novel-info-header']/h3/a//text()")
            )

            cover_rel = cls._first_str(
                item.xpath(".//div[contains(@class,'module-item-pic')]//img/@data-src")
            ) or cls._first_str(
                item.xpath(".//div[contains(@class,'module-item-pic')]//img/@src")
            )
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
                    author="-",  # Author is not present on the page
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )
        return results
