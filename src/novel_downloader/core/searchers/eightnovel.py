#!/usr/bin/env python3
"""
novel_downloader.core.searchers.eightnovel
--------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["eightnovel", "8novel"],
)
class EightnovelSearcher(BaseSearcher):
    site_name = "8novel"
    priority = 20
    BASE_URL = "https://www.8novel.com"
    SEARCH_URL = "https://www.8novel.com/search/"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from 8novel's search page.

        :param keyword: The search term to query on 8novel.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"key": keyword}
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
        Parse raw HTML from 8novel search results into list of SearchResult.

        :param html_str: Raw HTML string from 8novel search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        anchors = doc.xpath("//div[contains(@class,'picsize')]/a")
        results: list[SearchResult] = []

        for idx, a in enumerate(anchors):
            if limit is not None and idx >= limit:
                break

            # Extract book_id from href, e.g. '/novelbooks/6045'
            href = a.get("href", "").strip()
            book_id = href.rstrip("/").split("/")[-1]
            if not book_id:
                continue
            book_url = cls.BASE_URL + href

            img_src = a.xpath(".//img/@src")
            cover_url = img_src[0] if img_src else ""
            if cover_url.startswith("/"):
                cover_url = cls.BASE_URL + cover_url

            title = a.get("title", "").strip()

            eps = a.xpath(".//eps")
            word_count = eps[0].text_content().strip() if eps else "-"

            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author="-",
                    latest_chapter="-",
                    update_date="-",
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
