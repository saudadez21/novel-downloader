#!/usr/bin/env python3
"""
novel_downloader.plugins.common.searcher.sososhu
------------------------------------------------

"""

import logging
import re
from typing import ClassVar
from urllib.parse import unquote, urlencode, urlparse

from lxml import html
from novel_downloader.plugins.base.searcher import BaseSearcher
from novel_downloader.schemas import SearchResult

logger = logging.getLogger(__name__)


class SososhuSearcher(BaseSearcher):
    priority = 30

    site_name = "sososhu"
    SOSOSHU_KEY: ClassVar[str]
    BASE_URL: ClassVar[str]
    SEARCH_URL = "https://www.sososhu.com/"

    async def _fetch_html(self, keyword: str) -> str:
        params = {
            "q": keyword,
            "site": self.SOSOSHU_KEY,
        }
        try:
            return await self._fetch(self.SEARCH_URL, params=params)
        except Exception:
            logger.error(
                "Failed to fetch HTML for keyword '%s' from '%s'",
                keyword,
                self.SEARCH_URL,
            )
            return ""

    async def _fetch(self, url: str, params: dict[str, str]) -> str:
        full_url = self._build_url(url, params)
        parsed = urlparse(full_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        referer = full_url

        get_headers = {
            **self.session.headers,
            "Origin": origin,
            "Referer": origin,
        }

        async with self.session.get(full_url, headers=get_headers) as resp:
            resp.raise_for_status()
            resp_text = await self._response_to_str(resp)
            if "Checking your browser" not in resp_text:
                return resp_text

            ge_ua_p = None
            if "ge_ua_p" in resp.cookies:
                ge_ua_p = unquote(resp.cookies["ge_ua_p"].value)
            else:
                logger.debug("ge_ua_p cookie not found; cannot verify browser")
                return resp_text

        logger.debug("sososhu encountered anti-bot page, trying to verify...")

        nonce_match = re.search(r"var\s+nonce\s*=\s*(\d+)", resp_text)
        if not nonce_match:
            logger.debug("Could not find nonce in verification page")
            return resp_text
        nonce = int(nonce_match.group(1))
        logger.debug("Found nonce=%s, ge_ua_p=%s", nonce, ge_ua_p)

        sum_val = self.calc_sum(ge_ua_p, nonce)
        payload = urlencode({"sum": str(sum_val), "nonce": str(nonce)})
        post_headers = {
            **self.session.headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-GE-UA-Step": "prev",
            "Cookie": f"ge_ua_p={ge_ua_p}",
            "Origin": origin,
            "Referer": referer,
        }

        async with self.session.post(
            full_url, data=payload, headers=post_headers
        ) as verify_resp:
            verify_resp.raise_for_status()
            _verify_text = await self._response_to_str(verify_resp)

        async with self.session.get(url, params=params) as final_resp:
            final_resp.raise_for_status()
            final_text = await self._response_to_str(final_resp)

        logger.debug("Verification completed, content fetched.")
        return final_text

    def _parse_html(
        self, html_str: str, limit: int | None = None
    ) -> list[SearchResult]:
        doc = html.fromstring(html_str)
        rows = doc.xpath(
            "//div[contains(@class,'so_list')]//div[contains(@class,'hot')]//div[contains(@class,'item')]"
        )
        results: list[SearchResult] = []

        for idx, row in enumerate(rows):
            href = next(iter(row.xpath(".//dl/dt/a[1]/@href")), "")
            if not href:
                continue

            if limit is not None and idx >= limit:
                break

            book_url = self._restore_url(self._abs_url(href))
            book_id = self._url_to_id(book_url)

            title = self._first_str(row.xpath(".//dl/dt/a[1]/text()"))
            author = self._first_str(row.xpath(".//dl/dt/span[1]/text()"))
            cover_url = self._first_str(
                row.xpath(".//div[contains(@class,'image')]//img/@src")
            )

            results.append(
                SearchResult(
                    site=self.site_name,
                    book_id=book_id,
                    book_url=book_url,
                    cover_url=cover_url,
                    title=title,
                    author=author,
                    latest_chapter="-",
                    update_date="-",
                    word_count="-",
                    priority=self.priority + idx,
                )
            )
        return results

    @staticmethod
    def _restore_url(url: str) -> str:
        return url

    @staticmethod
    def _url_to_id(url: str) -> str:
        return url

    @staticmethod
    def calc_sum(cookie_value: str, nonce: int) -> int:
        total = 0
        for i, ch in enumerate(cookie_value):
            if ch.isalnum():  # JS /^[a-zA-Z0-9]$/
                total += ord(ch) * (nonce + i)
        return total
