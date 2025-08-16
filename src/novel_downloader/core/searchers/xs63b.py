#!/usr/bin/env python3
"""
novel_downloader.core.searchers.xs63b
-------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["xs63b"],
)
class Xs63bSearcher(BaseSearcher):
    site_name = "xs63b"
    priority = 30
    BASE_URL = "https://www.xs63b.com"
    SEARCH_URL = "https://www.xs63b.com/search/"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Xs63b's search page.

        :param keyword: The search term to query on Xs63b.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        headers = {
            "Host": "www.xs63b.com",
            "Origin": "https://www.xs63b.com",
            "Referer": "https://www.xs63b.com/",
        }
        try:
            async with (await cls._http_get(cls.BASE_URL, headers=headers)) as resp:
                base_html = await cls._response_to_str(resp)
            data = {
                "_token": cls._parse_token(base_html),
                "kw": keyword,
            }
            async with (
                await cls._http_post(cls.SEARCH_URL, data=data, headers=headers)
            ) as resp:
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
        """
        Parse raw HTML from Xs63b search results into list of SearchResult.

        :param html_str: Raw HTML string from Xs63b search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath("//div[@class='toplist']/ul/li")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            # title & URL (strip <em> highlights using XPath string())
            a_node = row.xpath(".//p[@class='s1']/a")
            book_url = a_node[0].get("href") if a_node else ""
            title = str(row.xpath("string(.//p[@class='s1']//a)")).strip()

            latest_chapter = cls._first_str(
                row.xpath(".//p[@class='s2']//a/text()")
            ).strip()
            author = cls._first_str(row.xpath(".//p[@class='s3']/text()"))
            word_count = cls._first_str(row.xpath(".//p[@class='s4']/text()"))
            update_date = cls._first_str(row.xpath(".//p[@class='s6']/text()"))
            book_id = cls._book_id_from_url(book_url)

            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results

    @staticmethod
    def _parse_token(html_str: str) -> str:
        doc = html.fromstring(html_str)
        vals = doc.xpath("//div[@id='search']//input[@name='_token']/@value")
        return vals[0].strip() if vals else ""

    @classmethod
    def _book_id_from_url(cls, url: str) -> str:
        tail = url.split("xs63b.com", 1)[-1]
        return tail.strip(" /").replace("/", "-")
