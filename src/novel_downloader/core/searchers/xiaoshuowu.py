#!/usr/bin/env python3
"""
novel_downloader.core.searchers.xiaoshuowu
------------------------------------------

"""

import logging
import re

from lxml import html

from novel_downloader.core.searchers.base import BaseSearcher
from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.models import SearchResult

logger = logging.getLogger(__name__)


@register_searcher(
    site_keys=["xiaoshuowu"],
)
class XiaoshuowuSearcher(BaseSearcher):
    site_name = "xiaoshuowu"
    priority = 30
    SEARCH_URL = "http://www.xiaoshuoge.info/modules/article/search.php"
    BOOK_ID_PATTERN = re.compile(r"/book/(\d+)/")
    CATA_ID_PATTERN = re.compile(r"/html/(\d+)/(\d+)/")

    @classmethod
    def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from Xiaoshuowu's search page.

        :param keyword: The search term to query on Xiaoshuowu.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        params = {"q": keyword}
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
        Parse raw HTML from Xiaoshuowu search results into list of SearchResult.

        :param html_str: Raw HTML string from Xiaoshuowu search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        doc = html.fromstring(html_str)
        rows = doc.xpath('//div[@class="c_row"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            # Title & Book ID
            title_elem = row.xpath('.//span[@class="c_subject"]/a')
            title = title_elem[0].text_content().strip() if title_elem else ""

            book_id = ""
            cata_elem = row.xpath(
                './/span[@class="c_subject"]/following-sibling::a[normalize-space(text())="目录"]'
            )
            if cata_elem:
                href = cata_elem[0].get("href", "")
                m = cls.CATA_ID_PATTERN.search(href)
                if m:
                    book_id = f"{m.group(1)}-{m.group(2)}"
            if not book_id and title_elem:
                href = title_elem[0].get("href", "")
                m2 = cls.BOOK_ID_PATTERN.search(href)
                if m2:
                    book_id = m2.group(1)
            if not book_id:
                continue

            author_nodes = row.xpath(
                './/span[@class="c_label"][normalize-space(text())="作者："]'
                '/following-sibling::span[@class="c_value"][1]/text()'
            )
            author = author_nodes[0].strip() if author_nodes else ""

            wc_nodes = row.xpath(
                './/span[@class="c_label"][normalize-space(text())="字数："]'
                '/following-sibling::span[@class="c_value"][1]/text()'
            )
            word_count = wc_nodes[0].strip() if wc_nodes else ""

            latest_nodes = row.xpath(
                './/span[@class="c_label"][normalize-space(text())="最新章节："]'
                '/following-sibling::span[@class="c_value"][1]//text()'
            )
            latest_chapter = latest_nodes[0].strip() if latest_nodes else ""

            update_nodes = row.xpath(
                './/span[@class="c_label"][normalize-space(text())="更新："]'
                '/following-sibling::span[@class="c_value"][1]/text()'
            )
            update_date = update_nodes[0].strip() if update_nodes else ""

            # Priority
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
