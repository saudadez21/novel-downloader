#!/usr/bin/env python3
"""
novel_downloader.plugins.base.searcher
--------------------------------------

Abstract base class providing common utilities for site-specific searchers.
"""

import abc
from typing import Any, ClassVar
from urllib.parse import quote_plus, urljoin

import aiohttp

from novel_downloader.infra.http_defaults import DEFAULT_USER_HEADERS
from novel_downloader.schemas import SearchResult


class BaseSearcher(abc.ABC):
    site_name: str
    priority: int = 1000
    BASE_URL: str = ""
    _session: ClassVar[aiohttp.ClientSession | None] = None

    @classmethod
    def configure(cls, session: aiohttp.ClientSession) -> None:
        cls._session = session

    @classmethod
    async def search(cls, keyword: str, limit: int | None = None) -> list[SearchResult]:
        html = await cls._fetch_html(keyword)
        if not html:
            return []
        return cls._parse_html(html, limit)

    @classmethod
    @abc.abstractmethod
    async def _fetch_html(cls, keyword: str) -> str:
        """
        Fetch raw HTML from search API or page

        :param keyword: The search term to query.
        :return: HTML text of the search results page, or an empty string on fail.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """
        Parse raw HTML from search API or page into list of SearchResult.

        :param html_str: Raw HTML string from search results page.
        :param limit: Maximum number of results to return, or None for all.
        :return: List of SearchResult dicts.
        """
        pass

    @classmethod
    def _http_get(
        cls,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> aiohttp.client._RequestContextManager:
        """
        Helper for GET requests with default headers.
        """
        session = cls._ensure_session()
        hdrs = {**DEFAULT_USER_HEADERS, **(headers or {})}
        return session.get(url, params=params, headers=hdrs, **kwargs)

    @classmethod
    def _http_post(
        cls,
        url: str,
        *,
        data: dict[str, str] | str | None = None,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> aiohttp.client._RequestContextManager:
        """
        Helper for POST requests with default headers.
        """
        session = cls._ensure_session()
        hdrs = {**DEFAULT_USER_HEADERS, **(headers or {})}
        return session.post(url, data=data, headers=hdrs, **kwargs)

    @classmethod
    def _ensure_session(cls) -> aiohttp.ClientSession:
        if cls._session is None:
            raise RuntimeError(
                f"{cls.__name__} has no aiohttp session. "
                "Call .configure(session) first."
            )
        return cls._session

    @staticmethod
    def _quote(q: str, encoding: str | None = None, errors: str | None = None) -> str:
        """URL-encode a query string safely."""
        return quote_plus(q, encoding=encoding, errors=errors)

    @staticmethod
    async def _response_to_str(
        resp: aiohttp.ClientResponse,
        encoding: str | None = None,
    ) -> str:
        """
        Read the full body of resp as text. First try the declared charset,
        then on UnicodeDecodeError fall back to a lenient utf-8 decode.
        """
        data: bytes = await resp.read()
        encodings = [
            encoding,
            resp.charset,
            "gb2312",
            "gb18030",
            "gbk",
            "utf-8",
        ]
        encodings_list: list[str] = [e for e in encodings if e]
        for enc in encodings_list:
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        encoding = encoding or "utf-8"
        return data.decode(encoding, errors="ignore")

    @staticmethod
    def _first_str(xs: list[str], replaces: list[tuple[str, str]] | None = None) -> str:
        replaces = replaces or []
        value: str = xs[0].strip() if xs else ""
        for replace in replaces:
            old, new = replace
            value = value.replace(old, new)
        return value.strip()

    @staticmethod
    def _build_url(base: str, params: dict[str, str]) -> str:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{query_string}"

    @classmethod
    def _abs_url(cls, url: str) -> str:
        if url.startswith("//"):
            return "https:" + url
        return (
            url
            if url.startswith(("http://", "https://"))
            else urljoin(cls.BASE_URL, url)
        )
