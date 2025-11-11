#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquge345.searcher
-------------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class Biquge345Searcher(BaseSearcher):
    site_name = "biquge345"
    priority = 50
    BASE_URL = "https://www.biquge345.com/"
    SEARCH_URL = "https://www.biquge345.com/s.php"

    async def _fetch_html(self, keyword: str) -> str:
        data = {
            "type": "articlename",
            "s": keyword,
            "submit": "",
        }
        try:
            async with self.session.post(self.SEARCH_URL, data=data) as resp:
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
        doc = html.fromstring(html_str)
        rows = doc.xpath('//ul[@class="search"]/li[not(@class)]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath('./span[@class="name"]/a/@href'))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = href.strip("/").split("/")[-1] or href
            book_url = self._abs_url(href)

            title = self._first_str(row.xpath('./span[@class="name"]/a/text()'))
            latest_chapter = self._first_str(row.xpath('./span[@class="jie"]/a/text()'))
            author = self._first_str(row.xpath('./span[@class="zuo"]/a/text()'))
            update_date = self._first_str(row.xpath('./span[@class="time"]/text()'))

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date=update_date,
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results
