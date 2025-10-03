#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.xiaoshuoge.searcher
-----------------------------------------------------

"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


class XiaoshuogeSearcher(BaseSearcher):
    site_name = "xiaoshuoge"
    priority = 30
    SEARCH_URL = "http://www.xiaoshuoge.info/modules/article/search.php"

    async def _fetch_html(self, keyword: str) -> str:
        params = {"q": keyword}
        try:
            async with self._http_get(self.SEARCH_URL, params=params) as resp:
                resp.raise_for_status()
                return await self._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                self.SEARCH_URL,
            )
            return ""

    def _parse_html(
        self, html_str: str, limit: int | None = None
    ) -> list[SearchResult]:
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
            href = self._first_str(row.xpath(".//span[@class='c_subject']/a/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # 'http://www.xiaoshuoge.info/book/374339/' -> "374339"
            book_id = href.split("book/")[-1].strip("/")
            book_url = self._abs_url(href)

            cover_rel = self._first_str(row.xpath(".//div[@class='fl']//img/@src"))
            cover_url = self._abs_url(cover_rel) if cover_rel else ""

            title = self._first_str(row.xpath(".//span[@class='c_subject']/a/text()"))

            author = (
                self._first_str(
                    row.xpath(
                        ".//div[@class='c_tag'][1]/span[@class='c_label'][contains(.,'作者')]/following-sibling::span[@class='c_value'][1]/text()"
                    )
                )
                or "-"
            )
            word_count = (
                self._first_str(
                    row.xpath(
                        ".//div[@class='c_tag'][1]/span[@class='c_label'][contains(.,'字数')]/following-sibling::span[@class='c_value'][1]/text()"
                    )
                )
                or "-"
            )

            latest_chapter = (
                self._first_str(
                    row.xpath(
                        ".//div[@class='c_tag'][last()]/span[@class='c_label'][contains(.,'最新')]/following-sibling::span[@class='c_value'][1]//a//text()"
                    )
                )
                or "-"
            )
            update_date = (
                self._first_str(
                    row.xpath(
                        ".//div[@class='c_tag'][last()]/span[@class='c_label'][contains(.,'更新')]/following-sibling::span[@class='c_value'][1]/text()"
                    )
                )
                or "-"
            )

            # Priority
            prio = self.priority + idx

            results.append(
                SearchResult(
                    site=self.site_name,
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
