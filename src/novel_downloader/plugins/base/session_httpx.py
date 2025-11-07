#!/usr/bin/env python3
"""
novel_downloader.plugins.base.session_httpx
-------------------------------------------
"""

import json
from pathlib import Path
from typing import Any, Unpack

import httpx

from novel_downloader.plugins.base.response import BaseResponse
from novel_downloader.plugins.base.session_base import (
    BaseSession,
    GetRequestKwargs,
    PostRequestKwargs,
)


class HttpxSession(BaseSession):
    """Session backend based on httpx providing async HTTP/1.1 and HTTP/2 support."""

    _session: httpx.AsyncClient | None

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        if self._session and not self._session.is_closed:
            return
        limits = httpx.Limits(
            max_keepalive_connections=self._max_connections,
            max_connections=self._max_connections,
        )
        proxy = self._build_proxy_config(
            self._proxy,
            self._proxy_user,
            self._proxy_pass,
        )

        self._session = httpx.AsyncClient(
            http2=self._http2,
            timeout=self._timeout,
            verify=self._verify_ssl,
            headers=self._headers,
            cookies=self._cookies,
            limits=limits,
            proxy=proxy,
            trust_env=self._trust_env,
        )

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        if self._session is None:
            return
        if not self._session.is_closed:
            await self._session.aclose()
        self._session = None

    async def get(
        self,
        url: str,
        *,
        allow_redirects: bool | None = None,
        verify: bool | None = None,
        encoding: str = "utf-8",
        **kwargs: Unpack[GetRequestKwargs],
    ) -> BaseResponse:
        if allow_redirects is not None:
            kwargs.setdefault("follow_redirects", allow_redirects)  # type: ignore[typeddict-item]

        r = await self.session.get(url, **kwargs)
        return BaseResponse(
            content=r.content,
            headers=r.headers,
            status=r.status_code,
            encoding=r.encoding or encoding,
        )

    async def post(
        self,
        url: str,
        *,
        allow_redirects: bool | None = None,
        verify: bool | None = None,
        encoding: str = "utf-8",
        **kwargs: Unpack[PostRequestKwargs],
    ) -> BaseResponse:
        if allow_redirects is not None:
            kwargs.setdefault("follow_redirects", allow_redirects)  # type: ignore[typeddict-item]

        r = await self.session.post(url, **kwargs)
        return BaseResponse(
            content=r.content,
            headers=r.headers,
            status=r.status_code,
            encoding=r.encoding or encoding,
        )

    def load_cookies(self, cookies_dir: Path, filename: str | None = None) -> bool:
        if self._session is None:
            return False

        filename = filename or "httpx.cookies"
        path = cookies_dir / filename
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False

        for item in data:
            name = item.get("name")
            value = item.get("value")
            domain = item.get("domain", "")
            path_ = item.get("path", "/")
            if name and value:
                self._session.cookies.set(name, value, domain=domain, path=path_)
        return True

    def save_cookies(self, cookies_dir: Path, filename: str | None = None) -> bool:
        if self._session is None:
            return False

        filename = filename or "httpx.cookies"
        cookies_dir.mkdir(parents=True, exist_ok=True)

        cookies: list[dict[str, str | None]] = []
        for cookie in self.session.cookies.jar:
            cookies.append(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path,
                }
            )
        (cookies_dir / filename).write_text(
            json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    def update_cookies(self, cookies: dict[str, str]) -> None:
        if self._session is None:
            return
        self._session.cookies.update(cookies)

    def get_cookie(self, key: str) -> str | None:
        """
        Retrieve the value of a cookie by name from the active session.

        :param key: Cookie name.
        :return: The cookie value if found, else None.
        """
        if self._session is None:
            return None

        value: str | None = self._session.cookies.get(key)
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="ignore")
            except Exception:
                return None
        return value

    @property
    def session(self) -> httpx.AsyncClient:
        """
        Return the active httpx.AsyncClient.

        :raises RuntimeError: If the session is uninitialized.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session

    @staticmethod
    def _build_proxy_config(
        proxy: str | None = None,
        proxy_user: str | None = None,
        proxy_pass: str | None = None,
    ) -> str | httpx.Proxy | None:
        """Builds proxy configuration."""
        if not proxy:
            return None

        if "@" in proxy:
            return proxy

        if proxy_user and proxy_pass:
            return httpx.Proxy(proxy, auth=(proxy_user, proxy_pass))

        return proxy
