#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.bixiange.searcher
------------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class BixiangeSearcher(BaseSearcher):
    site_name = "bixiange"
    priority = 30
    BASE_URL = "https://m.bixiange.me"
    SEARCH_URL = "https://m.bixiange.me/e/search/indexpage.php"

    async def _fetch_html(self, keyword: str) -> str:
        kw = self._quote(keyword, encoding="gbk", errors="replace")
        data = f"keyboard={kw}&show=title&classid=0"
        headers = {
            **self.session.headers,
            "Referer": "https://m.bixiange.me/",
            "Origin": "https://m.bixiange.me",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            async with self.session.post(
                self.SEARCH_URL, headers=headers, data=data
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
        rows = doc.xpath('//div[contains(@class, "list")]//li')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            if limit is not None and idx >= limit:
                break

            href = self._first_str(row.xpath('.//div[@class="cover"]/a/@href'))
            if not href:
                continue

            book_url = self._abs_url(href)
            # "/khjj/11945.html" -> "khjj-11945"
            # "/trxs/19408" -> "trxs-19408"
            href_path = href.strip("/").split(".", 1)[0].split("/")
            book_id = "-".join(href_path)

            cover_url = self._first_str(row.xpath('.//div[@class="cover"]//img/@src'))
            if cover_url:
                cover_url = self._abs_url(cover_url)

            title = self._first_str(row.xpath('.//div[@class="title"]//a/text()'))

            update_date = self._first_str(
                row.xpath(
                    './/div[@class="tips"]/span[contains(text(), "时间")]/text()'
                ),  # noqa: E501
                replaces=[("时间：", "")],
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author="-",
                    latest_chapter="-",
                    update_date=update_date,
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results
