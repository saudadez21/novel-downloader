#!/usr/bin/env python3
"""
novel_downloader.core.searchers.aaatxt
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
    site_keys=["aaatxt"],
)
class AaatxtSearcher(BaseSearcher):
    site_name = "aaatxt"
    priority = 500
    SEARCH_URL = "http://www.aaatxt.com/search.php"

    @classmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Aaatxt's search page.

        :param keyword: The search term to query on Aaatxt.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        # gbk / gb2312
        params = {
            "keyword": cls._quote(keyword, encoding="gb2312", errors="replace"),
            "submit": cls._quote("搜 索", encoding="gb2312", errors="replace"),
        }
        full_url = cls._build_url(cls.SEARCH_URL, params)  # need build manually
        headers = {
            "Host": "www.aaatxt.com",
            "Referer": "http://www.aaatxt.com/",
        }
        try:
            async with (await cls._http_get(full_url, headers=headers)) as resp:
                return await cls._response_to_str(resp, "gb2312")
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
        Parse raw HTML from Aaatxt search results into list of SearchResult.

        :param html_str: Raw HTML string from Aaatxt search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath("//div[@class='sort']//div[@class='list']/table")
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break
            # Cover and URL
            cover_url = row.xpath(".//td[@class='cover']/a/img/@src")[0]
            book_url = row.xpath(".//td[@class='name']/h3/a/@href")[0]
            book_id = book_url.rstrip(".html").split("/")[-1]
            title = row.xpath(".//td[@class='name']/h3/a/text()")[0].strip()

            # Parse size and uploader from the size cell
            size_cell = row.xpath(".//td[@class='size']")[0].text_content().strip()
            # Extract word count using regex (e.g., '465K')
            m_wc = re.search(r"大小:([^\s\xa0]+)", size_cell)
            word_count = m_wc.group(1) if m_wc else "-"

            # Extract author/uploader (after '上传:')
            m_auth = re.search(r"上传:([^\s\xa0]+)", size_cell)
            author = m_auth.group(1) if m_auth else "-"

            # Intro for update date
            intro = row.xpath(".//td[@class='intro']")[0].text_content()
            update_date = "-"
            if "更新:" in intro:
                parts = intro.split("更新:", 1)
                date_part = parts[1].strip()
                match = re.match(r"(\d{4}-\d{2}-\d{2})", date_part)
                if match:
                    update_date = match.group(1)

            results.append(
                SearchResult(
                    site=cls.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date=update_date,
                    word_count=word_count,
                    priority=cls.priority + idx,
                )
            )
        return results
