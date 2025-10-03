#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.piaotia.searcher
-----------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class PiaotiaSearcher(BaseSearcher):
    site_name = "piaotia"
    priority = 30
    SEARCH_URL = "https://www.piaotia.com/modules/article/search.php"

    async def _fetch_html(self, keyword: str) -> str:
        # data = {
        #     "searchtype": "articlename",
        #     # "searchtype": "author",
        #     # "searchtype": "keywords",
        #     "searchkey": self._quote(keyword, encoding="gbk", errors='replace'),
        #     "Submit": self._quote(" 搜 索 ", encoding="gbk", errors='replace'),
        # }
        searchtype = "articlename"
        searchkey = self._quote(keyword, encoding="gbk", errors="replace")
        submit = self._quote(" 搜 索 ", encoding="gbk", errors="replace")
        body = f"searchtype={searchtype}&searchkey={searchkey}&Submit={submit}"
        headers = {
            "Origin": "https://www.piaotia.com",
            "Referer": "https://www.piaotia.com",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with self._http_post(
                self.SEARCH_URL, data=body, headers=headers
            ) as resp:
                resp.raise_for_status()
                return await self._response_to_str(resp, encoding="gbk")
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
        rows = doc.xpath('//table[@class="grid"]//tr[td]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath("./td[1]/a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # "https://www.piaotia.com/bookinfo/14/14767.html" -> "14-14767"
            book_id = href.rstrip(".html").split("bookinfo/")[-1].replace("/", "-")
            book_url = self._abs_url(href)

            title = self._first_str(row.xpath("./td[1]/a[1]//text()"))

            latest_chapter = self._first_str(row.xpath("./td[2]/a[1]//text()")) or "-"

            author = self._first_str(row.xpath("./td[3]//text()")) or "-"
            word_count = self._first_str(row.xpath("./td[4]//text()")) or "-"
            update_date = self._first_str(row.xpath("./td[5]//text()")) or "-"

            # Compute priority incrementally
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
