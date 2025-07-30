#!/usr/bin/env python3
"""
novel_downloader.core.searchers.base
------------------------------------

"""

import abc
from typing import Any
from urllib.parse import quote_plus

import requests

from novel_downloader.core.interfaces import SearcherProtocol
from novel_downloader.models import SearchResult
from novel_downloader.utils.constants import DEFAULT_USER_HEADERS


class BaseSearcher(abc.ABC, SearcherProtocol):
    site_name: str
    _session = requests.Session()
    _DEFAULT_TIMEOUT: tuple[int, int] = (5, 10)

    @classmethod
    def search(cls, keyword: str, limit: int | None = None) -> list[SearchResult]:
        html = cls._fetch_html(keyword)
        return cls._parse_html(html, limit)

    @classmethod
    @abc.abstractmethod
    def _fetch_html(cls, keyword: str) -> str:
        """Get raw HTML from search API or page"""
        pass

    @classmethod
    @abc.abstractmethod
    def _parse_html(cls, html_str: str, limit: int | None = None) -> list[SearchResult]:
        """Parse HTML into standard search result list"""
        pass

    @classmethod
    def _http_get(
        cls,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: tuple[int, int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Helper for GET requests with default headers, timeout, and error-raising.
        """
        hdrs = {**DEFAULT_USER_HEADERS, **(headers or {})}
        resp = cls._session.get(
            url,
            params=params,
            headers=hdrs,
            timeout=timeout or cls._DEFAULT_TIMEOUT,
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    @classmethod
    def _http_post(
        cls,
        url: str,
        *,
        data: dict[str, str] | str | None = None,
        headers: dict[str, str] | None = None,
        timeout: tuple[int, int] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Helper for POST requests with default headers, timeout, and error-raising.
        """
        hdrs = {**DEFAULT_USER_HEADERS, **(headers or {})}
        resp = cls._session.post(
            url,
            data=data,
            headers=hdrs,
            timeout=timeout or cls._DEFAULT_TIMEOUT,
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    @staticmethod
    def _quote(q: str, encoding: str | None = None, errors: str | None = None) -> str:
        """URL-encode a query string safely."""
        return quote_plus(q, encoding=encoding, errors=errors)

    @staticmethod
    def _first_str(xs: list[str], replaces: list[tuple[str, str]] | None = None) -> str:
        replaces = replaces or []
        value: str = xs[0].strip() if xs else ""
        for replace in replaces:
            old, new = replace
            value = value.replace(old, new)
        return value

    @staticmethod
    def _build_url(base: str, params: dict[str, str]) -> str:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{query_string}"
