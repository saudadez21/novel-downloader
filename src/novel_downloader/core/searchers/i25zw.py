#!/usr/bin/env python3
"""
novel_downloader.core.searchers.i25zw
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
    site_keys=["i25zw"],
)
class I25zwSearcher(BaseSearcher):
    site_name = "i25zw"
    priority = 30
    SEARCH_URL = "https://www.i25zw.com/search.html"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from I25zw's search page.

        :param keyword: The search term to query on I25zw.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        payload = {
            "searchkey": keyword,
            "searchtype": "all",
            "Submit": "",
        }
        try:
            response = cls._http_post(cls.SEARCH_URL, data=payload)
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
        Parse raw HTML from I25zw search results into list of SearchResult.

        :param html_str: Raw HTML string from I25zw search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath("//div[@id='alistbox']")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break
            prio = cls.priority + idx

            # Extract book_id from picture link or title link
            pic_href = row.xpath(".//div[@class='pic']/a/@href")
            if pic_href:
                m = re.search(r"/book/(\d+)\.html", pic_href[0])
                book_id = m.group(1) if m else ""
            else:
                title_href = row.xpath(".//div[@class='title']/h2/a/@href")
                book_id = title_href[0].strip("/").strip() if title_href else ""

            # Title text
            title_nodes = row.xpath(".//div[@class='title']/h2/a/text()")
            title = title_nodes[0].strip() if title_nodes else ""

            # Author
            auth_nodes = row.xpath(".//div[@class='title']/span/text()")
            author = auth_nodes[0].replace("作者：", "").strip() if auth_nodes else ""

            # Latest chapter
            latest_nodes = row.xpath(".//div[@class='sys']//li/a/text()")
            latest_chapter = latest_nodes[0].strip() if latest_nodes else ""

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date="-",
                    word_count="-",
                    priority=prio,
                )
            )

        return results
