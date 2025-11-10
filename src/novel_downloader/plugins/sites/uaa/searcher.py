#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.uaa.searcher
-------------------------------------------
"""

import logging

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class UaaSearcher(BaseSearcher):
    site_name = "uaa"
    priority = 500
    BASE_URL = "https://www.uaa.com"
    SEARCH_URL = "https://www.uaa.com/novel/list"

    @property
    def nsfw(self) -> bool:
        return True

    async def _fetch_html(self, keyword: str) -> str:
        params = {"searchType": "1", "keyword": self._quote(keyword)}
        try:
            url = self._build_url(self.SEARCH_URL, params=params)
            print(f"url = '{url}'")
            async with self.session.get(url) as resp:
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
        items = doc.xpath('//li[contains(@class, "novel_li_2")]')
        # '//div[@class="novel_list_box"]//li[contains(@class, "novel_li_2")]'
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            href = self._first_str(item.xpath('.//div[@class="cover_box"]//a/@href'))
            if not href:
                continue

            if limit is not None and len(results) >= limit:
                break

            book_id = href.split("id=")[-1]
            book_url = self._abs_url(href)

            title = self._first_str(item.xpath('.//div[@class="title"]/a/text()'))
            cover_url = self._first_str(
                item.xpath('.//img[contains(@class,"cover")]/@src')
            )
            latest_chapter = self._first_str(
                item.xpath(
                    './/div[contains(@class,"update_state_box")]//span[contains(@class,"update_desc")]/text()'
                )
            )
            word_count = self._first_str(
                item.xpath(
                    './/div[@class="other_box"]/span[contains(text(),"字")]/text()'
                )
            )

            author = self._first_str(
                item.xpath(
                    './/div[contains(@class,"info_box")][contains(.,"作者")]/a/text()'
                )
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter=latest_chapter,
                    update_date="-",
                    word_count=word_count,
                    priority=self.priority + idx,
                )
            )
        return results
