#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xiguashuwu.searcher
--------------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class XiguashuwuSearcher(BaseSearcher):
    site_name = "xiguashuwu"
    priority = 500
    BASE_URL = "https://www.xiguashuwu.com"
    SEARCH_URL = "https://www.xiguashuwu.com/search/{query}"

    async def _fetch_html(self, keyword: str) -> str:
        url = self.SEARCH_URL.format(query=self._quote(keyword))
        headers = {
            "Referer": "https://www.xiguashuwu.com/search/",
        }
        try:
            async with self._http_get(url, headers=headers) as resp:
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
        rows = doc.xpath('//div[@class="SHsectionThree-middle"]/p')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(
                row.xpath(".//a[starts-with(@href,'/book/')][1]/@href")
            ) or self._first_str(row.xpath(".//a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/book/184974/iszip/0/' -> "184974"
            book_id = href.split("/book/")[-1].split("/")[0]
            book_url = self._abs_url(href)

            title = (
                self._first_str(
                    row.xpath(".//a[starts-with(@href,'/book/')][1]//text()")
                )
                or self._first_str(row.xpath(".//a[1]//text()"))
                or "-"
            )

            author = (
                self._first_str(
                    row.xpath(".//a[starts-with(@href,'/writer/')][1]//text()")
                )
                or self._first_str(row.xpath(".//a[2]//text()"))
                or "-"
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="-",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results
