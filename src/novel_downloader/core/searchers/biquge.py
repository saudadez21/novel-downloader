#!/usr/bin/env python3
"""
novel_downloader.core.searchers.biquge
--------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["biquge", "bqg"],
)
class BiqugeSearcher(BaseSearcher):
    site_name = "biquge"
    priority = 30
    SEARCH_URL = "http://www.b520.cc/modules/article/search.php"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Biquge's search page.

        :param keyword: The search term to query on Biquge.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"searchkey": keyword}
        try:
            response = cls._http_get(cls.SEARCH_URL, params=params)
            return response.text
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                cls.SEARCH_URL,
                exc_info=True,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from Biquge search results into list of SearchResult.

        :param html_str: Raw HTML string from Biquge search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//table[@class="grid"]//tr[position()>1]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break
            # Title and book_id
            title_elem = row.xpath(".//td[1]/a")[0]
            title = title_elem.text_content().strip()
            href = title_elem.get("href", "").strip("/")
            book_id = href.split("/")[0] if href else ""
            if not book_id:
                continue

            latest_elem = row.xpath(".//td[2]/a")
            latest_chapter = (
                latest_elem[0].text_content().strip() if latest_elem else "-"
            )

            author = row.xpath(".//td[3]")[0].text_content().strip()

            word_count = row.xpath(".//td[4]")[0].text_content().strip()
            update_date = row.xpath(".//td[5]")[0].text_content().strip()
            # Compute priority
            prio = cls.priority + idx

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
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
