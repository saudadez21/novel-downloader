#!/usr/bin/env python3
"""
novel_downloader.core.searchers.piaotia
---------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["piaotia"],
)
class PiaotiaSearcher(BaseSearcher):
    site_name = "piaotia"
    priority = 30
    SEARCH_URL = "https://www.piaotia.com/modules/article/search.php"

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Piaotia's search page.

        :param keyword: The search term to query on Piaotia.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        # data = {
        #     "searchtype": "articlename",
        #     # "searchtype": "author",
        #     # "searchtype": "keywords",
        #     "searchkey": cls._quote(keyword, encoding="gbk", errors='replace'),
        #     "Submit": cls._quote(" 搜 索 ", encoding="gbk", errors='replace'),
        # }
        searchtype = "articlename"
        searchkey = cls._quote(keyword, encoding="gbk", errors="replace")
        submit = cls._quote(" 搜 索 ", encoding="gbk", errors="replace")
        body = f"searchtype={searchtype}&searchkey={searchkey}&Submit={submit}"
        headers = {
            "Origin": "https://www.piaotia.com",
            "Referer": "https://www.piaotia.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            response = cls._http_post(cls.SEARCH_URL, data=body, headers=headers)
            response.encoding = "gbk"
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
        Parse raw HTML from Piaotia search results into list of SearchResult.

        :param html_str: Raw HTML string from Piaotia search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//table[@class="grid"]//tr[td]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break
            # Title and book_id
            link = row.xpath("./td[1]/a")[0]
            href = link.get("href", "").strip()
            title = link.text_content().strip()

            match = re.search(r"/bookinfo/([^/]+/[^/]+)\.html", href)
            book_id = match.group(1) if match else href.rstrip(".html").split("/")[-1]
            if not book_id:
                continue
            book_id = book_id.replace("/", "-")

            latest_elems = row.xpath("./td[2]/a")
            latest_chapter = (
                latest_elems[0].text_content().strip() if latest_elems else "-"
            )

            author_nodes = row.xpath("./td[3]/text()")
            author = author_nodes[0].strip() if author_nodes else ""

            word_count = row.xpath("./td[4]")[0].text_content().strip()
            update_date = row.xpath("./td[5]")[0].text_content().strip()

            # Compute priority incrementally
            prio = cls.priority + idx
            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
