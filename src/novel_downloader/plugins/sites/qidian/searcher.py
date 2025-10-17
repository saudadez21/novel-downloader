#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.searcher
----------------------------------------------

"""

import json
import logging

from lxml import html

from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


@registrar.register_searcher()
class QidianSearcher(BaseSearcher):
    site_name = "qidian"
    priority = 0
    SEARCH_URL = "https://www.qidian.com/so/{query}.html"
    _E1_VAL = {"l6": "", "l7": "", "l1": "", "l3": "", "pid": "qd_p_qidian", "eid": ""}

    async def _fetch_html(self, keyword: str) -> str:
        url = self.SEARCH_URL.format(query=self._quote(keyword))
        try:
            cookies = {
                "e1": self._quote(json.dumps(self._E1_VAL)),
            }
            async with self._http_get(url, cookies=cookies) as resp:
                resp.raise_for_status()
                return await self._response_to_str(resp)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                url,
            )
            return ""

    def _parse_html(
        self, html_str: str, limit: int | None = None
    ) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        items = doc.xpath(
            '//div[@id="result-list"]//li[contains(@class, "res-book-item")]'
        )
        results: list[SearchResult] = []

        for idx, item in enumerate(items):
            book_id = self._first_str(item.xpath("./@data-bid"))
            book_url = self._first_str(
                item.xpath('.//h3[contains(@class,"book-info-title")]//a/@href')
            )
            if not book_id or not book_url:
                continue
            if limit is not None and idx >= limit:
                break

            cover_url = self._first_str(
                item.xpath('.//div[contains(@class,"book-img-box")]//img/@src')
            )
            book_url = self._abs_url(book_url)
            cover_url = self._abs_url(cover_url)

            title = self._first_str(
                item.xpath('.//h3[contains(@class,"book-info-title")]//a/@title'),
                replaces=[("在线阅读", "")],
            )
            author = self._first_str(
                item.xpath(
                    './/p[contains(@class,"author")]//a[contains(@class,"name")]/text()'
                    ' | .//p[contains(@class,"author")]//i/text()'
                )
            )
            latest_chapter = self._first_str(
                item.xpath('.//p[contains(@class,"update")]//a/text()'),
                replaces=[("最新更新", "")],
            )
            update_date = self._first_str(
                item.xpath('.//p[contains(@class,"update")]//span/text()')
            )
            word_count = self._first_str(
                item.xpath(
                    './/div[contains(@class,"book-right-info")]//div[contains(@class,"total")]/p[1]/span/text()'
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
                    update_date=update_date,
                    word_count=word_count,
                    priority=self.priority + idx,
                )
            )
        return results
