#!/usr/bin/env python3
"""
novel_downloader.core.searchers.ixdzs8
--------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["ixdzs8"],
)
class Ixdzs8Searcher(BaseSearcher):
    site_name = "ixdzs8"
    priority = 30
    BASE_URL = "https://ixdzs8.com"
    SEARCH_URL = "https://ixdzs8.com/bsearch"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Ixdzs8's search page.

        :param keyword: The search term to query on Ixdzs8.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"q": keyword}
        try:
            async with (await cls._http_get(cls.SEARCH_URL, params=params)) as resp:
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
        Parse raw HTML from Ixdzs8 search results into list of SearchResult.

        :param html_str: Raw HTML string from Ixdzs8 search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath("//ul[contains(@class,'u-list')]/li[contains(@class,'burl')]")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            # Book path & ID
            book_path = (row.get("data-url") or "").strip()
            if not book_path:
                book_path = "".join(
                    row.xpath(".//h3[contains(@class,'bname')]//a/@href")
                ).strip()
            # Ensure leading slash
            if (
                book_path
                and not book_path.startswith("/")
                and book_path.startswith("read/")
            ):
                book_path = "/" + book_path
            m = re.search(r"/read/(\d+)/?", book_path)
            book_id = m.group(1) if m else ""

            # Absolute book URL
            book_url = (
                f"{cls.BASE_URL}{book_path}"
                if book_path.startswith("/")
                else (book_path or "")
            )

            # Cover, title, author, counts
            cover_url = cls._clean_text(
                "".join(row.xpath(".//div[contains(@class,'l-img')]//img/@src"))
            )
            title = cls._clean_text(
                "".join(row.xpath(".//h3[contains(@class,'bname')]/a/@title"))
            )
            author = cls._clean_text(
                "".join(row.xpath(".//span[contains(@class,'bauthor')]//a/text()"))
            )
            word_count = cls._clean_text(
                "".join(row.xpath(".//span[contains(@class,'size')]/text()"))
            )

            # Latest chapter title and update time
            latest_chapter = cls._clean_text(
                "".join(
                    row.xpath(
                        ".//p[contains(@class,'l-last')]//span[contains(@class,'l-chapter')]/text()"
                    )
                )
            )
            update_date = cls._clean_text(
                "".join(
                    row.xpath(
                        ".//p[contains(@class,'l-last')]//span[contains(@class,'l-time')]/text()"
                    )
                )
            )

            # Fallbacks
            if not title and book_id:
                title = f"Book {book_id}"

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

    @staticmethod
    def _clean_text(s: str) -> str:
        return re.sub(
            r"\s+", " ", (s or "").replace("\xa0", " ").replace("\u3000", " ")
        ).strip()
