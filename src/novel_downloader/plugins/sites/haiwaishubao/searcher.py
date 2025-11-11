#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.haiwaishubao.searcher
----------------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class HaiwaishubaoSearcher(BaseSearcher):
    site_name = "haiwaishubao"
    priority = 500
    BASE_URL = "https://www.haiwaishubao.com/"
    SEARCH_URL = "https://www.haiwaishubao.com/search/"

    @property
    def nsfw(self) -> bool:
        return True

    async def _fetch_html(self, keyword: str) -> str:
        payload = {
            "searchkey": keyword,
            "searchtype": "all",
            "submit": "",
        }
        headers = {
            **self.session.headers,
            "Host": "www.haiwaishubao.com",
            "Referer": "https://www.haiwaishubao.com",
        }
        try:
            async with self.session.post(
                self.SEARCH_URL, data=payload, headers=headers
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
        rows = doc.xpath('//div[contains(@class,"SHsectionThree-middle")]/p')
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = self._first_str(row.xpath('.//a[contains(@href,"/book/")]/@href'))
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            # "/book/103432/" -> "7631"
            book_id = href.strip("/").rsplit("/", 1)[-1]
            book_url = self._abs_url(href)

            title = self._first_str(row.xpath('.//a[contains(@href,"/book/")]/text()'))
            author = self._first_str(
                row.xpath('.//a[contains(@href,"/author/")]/text()')
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url="",
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        print(results)
        return results
