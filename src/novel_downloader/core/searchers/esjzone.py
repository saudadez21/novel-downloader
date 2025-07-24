#!/usr/bin/env python3
"""
novel_downloader.core.searchers.esjzone
---------------------------------------

"""

import logging

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["esjzone"],
)
class EsjzoneSearcher(BaseSearcher):
    site_name = "esjzone"
    priority = 30
    SEARCH_URL = "https://www.esjzone.cc/tags/{query}/"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Esjzone's search page.

        :param keyword: The search term to query on Esjzone.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        url = cls.SEARCH_URL.format(query=cls._quote(keyword))
        try:
            response = cls._http_get(url)
            return response.text
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                url,
                exc_info=True,
            )
            return ""

    @classmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from Esjzone search results into list of SearchResult.

        :param html_str: Raw HTML string from Esjzone search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        cards = doc.xpath('//div[contains(@class,"card-body")]')
        results: list[SearchResult] = []

        for idx, card in enumerate(cards):
            if limit is not None and idx >= limit:
                break
            # Title and book_id
            link = card.xpath('.//h5[@class="card-title"]/a')[0]
            title = link.text_content().strip()
            href = link.get("href", "")
            # href format: /detail/<book_id>.html
            book_id = href.strip("/").replace("detail/", "").replace(".html", "")
            # Author
            author_link = card.xpath('.//div[@class="card-author"]/a')[0]
            author = author_link.text_content().strip()
            # Compute priority incrementally
            prio = cls.priority + idx
            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    title=title,
                    author=author,
                    priority=prio,
                )
            )
        return results
