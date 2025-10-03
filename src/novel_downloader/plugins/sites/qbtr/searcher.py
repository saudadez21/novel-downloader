#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qbtr.searcher
--------------------------------------------

"""

import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class QbtrSearcher(BaseSearcher):
    site_name = "qbtr"
    priority = 30
    BASE_URL = "https://www.qbtr.cc"
    SEARCH_URL = "https://www.qbtr.cc/e/search/index.php"

    async def _fetch_html(self, keyword: str) -> str:
        keyboard = self._quote(keyword, encoding="gbk", errors="replace")
        show = "title"
        classid = "0"
        body = f"keyboard={keyboard}&show={show}&classid={classid}"
        headers = {
            "Origin": "https://www.qbtr.cc",
            "Referer": "https://www.qbtr.cc/",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with self._http_post(
                self.SEARCH_URL, data=body, headers=headers
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
        rows = doc.xpath('//div[@class="books m-cols"]/div[@class="bk"]')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath(".//h3/a[1]/@href"))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # '/tongren/8850.html' -> "tongren-8850"
            book_id = href.strip("/").split(".")[0].replace("/", "-")
            book_url = self._abs_url(href)

            title = self._first_str(row.xpath(".//h3/a[1]//text()"))

            author = (
                self._first_str(
                    row.xpath(".//div[contains(@class,'booknews')]/text()"),
                    replaces=[("作者：", "")],
                )
                or "-"
            )

            update_date = (
                self._first_str(
                    row.xpath(
                        ".//div[contains(@class,'booknews')]/label[contains(@class,'date')]/text()"
                    )
                )
                or "-"
            )

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
                    latest_chapter="-",
                    update_date=update_date,
                    word_count="-",
                    priority=prio,
                )
            )
        return results
