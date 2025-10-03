#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.b520.searcher
--------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class B520Searcher(BaseSearcher):
    site_name = "b520"
    priority = 30
    BASE_URL = "http://www.b520.cc/"
    SEARCH_URL = "http://www.b520.cc/modules/article/search.php"

    async def _fetch_html(self, keyword: str) -> str:
        params = {"searchkey": keyword}
        headers = {
            "Referer": "http://www.b520.cc/",
        }
        try:
            async with self._http_get(
                self.SEARCH_URL, params=params, headers=headers
            ) as resp:
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
        rows = doc.xpath('//table[@class="grid"]//tr[position()>1]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath(".//td[1]/a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_id = href.strip("/").split("/")[-1]
            book_url = self._abs_url(href)

            title = self._first_str(row.xpath(".//td[1]/a[1]/text()"))

            latest_chapter = self._first_str(row.xpath(".//td[2]/a[1]/text()")) or "-"

            author = self._first_str(row.xpath(".//td[3]//text()"))
            word_count = self._first_str(row.xpath(".//td[4]//text()"))
            update_date = self._first_str(row.xpath(".//td[5]//text()"))

            # Compute priority
            prio = self.priority + idx

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
                    word_count=word_count,
                    priority=prio,
                )
            )
        return results
