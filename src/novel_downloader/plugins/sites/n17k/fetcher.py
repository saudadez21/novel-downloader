#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n17k.fetcher
-------------------------------------------
"""

import base64
import random
import re
from typing import Any

import aiohttp
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import FetcherConfig


@registrar.register_fetcher()
class N17kSession(GenericSession):
    """
    A session class for interacting with the 17K小说网 (www.17k.com) novel.
    """

    # fmt: off
    site_name: str = "n17k"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.17k.com/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.17k.com/list/{book_id}.html"
    CHAPTER_URL = "https://www.17k.com/chapter/{book_id}/{chapter_id}.html"

    _RE_ARG_1 = re.compile(
        r"var\s+arg1\s*=\s*(['\"])\s*([0-9A-F]+)\s*\1",
        re.IGNORECASE
    )
    _SEC: bytes = base64.b64decode(b"MAAXYACFYAYGFQFTMANpACeAA3U=")
    _ORDER_IDX = [
        14, 34, 28, 23, 32, 15, 0, 37, 9, 8, 18, 30, 39, 26, 21, 22, 24, 12, 5, 10,
        38, 17, 19, 7, 13, 20, 31, 25, 1, 29, 6, 3, 16, 4, 2, 27, 33, 36, 11, 35,
    ]
    # fmt: on

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        cookies = dict(cookies or {})
        key = self._d("R1VJRA==")
        if key not in cookies:
            cookies[key] = self._create_guid()
        super().__init__(config, cookies, **kwargs)

    async def fetch(
        self,
        url: str,
        encoding: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Fetch the content from the given URL asynchronously, with retry support.

        :param url: The target URL to fetch.
        :param kwargs: Additional keyword arguments to pass to `session.get`.
        :return: The response body as text.
        :raises: aiohttp.ClientError on final failure.
        """
        if self._rate_limiter:
            await self._rate_limiter.wait()

        for attempt in range(self._retry_times + 1):
            try:
                async with self.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    text = await self._response_to_str(resp, encoding)

                match = self._RE_ARG_1.search(text)
                if match:
                    arg1_val = match.group(2).strip()
                    reordered = self._reorder(arg1_val)
                    arg2_val = self._xor_hex(reordered)

                    self.update_cookies({self._d("YWN3X3NjX192Mg=="): arg2_val})

                    async with self.get(url, **kwargs) as resp2:
                        resp2.raise_for_status()
                        return await self._response_to_str(resp2, encoding)

                return text

            except aiohttp.ClientError:
                if attempt < self._retry_times:
                    await async_jitter_sleep(
                        self._backoff_factor,
                        mul_spread=1.1,
                        max_sleep=self._backoff_factor + 2,
                    )
                    continue
                raise

        raise RuntimeError("Unreachable code reached in fetch()")

    @classmethod
    def _reorder(cls, s: str) -> str:
        """Reorders a hex string based on a predefined order array."""
        return "".join(s[i] for i in cls._ORDER_IDX)

    @classmethod
    def _xor_hex(cls, a: str) -> str:
        """
        Performs XOR between two equal-length hex strings.

        :param a: hex string.
        :return: XOR result as hex string.
        """
        a_bytes = bytes.fromhex(a)
        return bytes(x ^ y for x, y in zip(a_bytes, cls._SEC, strict=False)).hex()

    @staticmethod
    def _create_guid() -> str:
        """
        Generates a GUID-like string

        :return: A random GUID string.
        """
        template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        return "".join(
            format(random.randint(0, 15), "x")
            if ch == "x"
            else format((random.randint(0, 15) & 0x3) | 0x8, "x")
            if ch == "y"
            else ch
            for ch in template
        )

    @staticmethod
    def _d(b: str) -> str:
        return base64.b64decode(b).decode()
