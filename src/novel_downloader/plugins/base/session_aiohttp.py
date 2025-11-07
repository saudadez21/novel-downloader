#!/usr/bin/env python3
"""
novel_downloader.plugins.base.session_aiohttp
---------------------------------------------
"""

import json
from pathlib import Path
from typing import Any, Unpack

import aiohttp

from novel_downloader.plugins.base.response import BaseResponse
from novel_downloader.plugins.base.session_base import (
    BaseSession,
    GetRequestKwargs,
    PostRequestKwargs,
)


class AiohttpSession(BaseSession):
    """Session backend implemented with aiohttp for asynchronous HTTP requests."""

    _session: aiohttp.ClientSession | None

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        if self._session and not self._session.closed:
            return

        proxy_auth: aiohttp.BasicAuth | None = None
        if self._proxy_user and self._proxy_pass:
            self._proxy_auth = aiohttp.BasicAuth(self._proxy_user, self._proxy_pass)

        timeout = aiohttp.ClientTimeout(total=self._timeout)
        connector = aiohttp.TCPConnector(
            ssl=self._verify_ssl,
            limit_per_host=self._max_connections,
        )

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._headers,
            cookies=self._cookies,
            trust_env=self._trust_env,
            proxy=self._proxy,
            proxy_auth=proxy_auth,
        )

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        if self._session and not self._session.closed:
            await self._session.close()
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
        if verify is not None:
            kwargs.setdefault("ssl", verify)  # type: ignore[typeddict-item]
        if allow_redirects is not None:
            kwargs.setdefault("allow_redirects", allow_redirects)  # type: ignore[typeddict-item]

        async with self.session.get(url, **kwargs) as r:
            content = await r.read()
            return BaseResponse(
                content=content,
                headers=r.headers,
                status=r.status,
                encoding=r.charset or encoding,
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
        if verify is not None:
            kwargs.setdefault("ssl", verify)  # type: ignore[typeddict-item]
        if allow_redirects is not None:
            kwargs.setdefault("allow_redirects", allow_redirects)  # type: ignore[typeddict-item]

        async with self.session.post(url, **kwargs) as r:
            content = await r.read()
            return BaseResponse(
                content=content,
                headers=r.headers,
                status=r.status,
                encoding=r.charset or encoding,
            )

    def load_cookies(self, cookies_dir: Path, filename: str | None = None) -> bool:
        if self._session is None:
            return False

        filename = filename or "aiohttp.cookies"
        path = cookies_dir / filename
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cookies = {c["name"]: c["value"] for c in data}
        except Exception:
            return False

        self._session.cookie_jar.update_cookies(cookies)
        return True

    def save_cookies(self, cookies_dir: Path, filename: str | None = None) -> bool:
        if self._session is None or self._session.cookie_jar is None:
            return False

        filename = filename or "aiohttp.cookies"
        cookies_dir.mkdir(parents=True, exist_ok=True)

        cookies: list[dict[str, str | None]] = []
        for cookie in self._session.cookie_jar:
            cookies.append(
                {
                    "name": cookie.key,
                    "value": cookie.value,
                }
            )

        (cookies_dir / filename).write_text(
            json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    def update_cookies(self, cookies: dict[str, str]) -> None:
        if self._session is None:
            return
        self._session.cookie_jar.update_cookies(cookies)

    def get_cookie(self, key: str) -> str | None:
        """
        Retrieve the value of a cookie by name from the active session.

        :param key: Cookie name.
        :return: The cookie value if found, else None.
        """
        if self._session is None:
            return None

        jar = self._session.cookie_jar
        for cookie in jar:
            if cookie.key == key:
                value: str = cookie.value
                return value
        return None

    @property
    def session(self) -> aiohttp.ClientSession:
        """
        Return the active aiohttp.ClientSession.

        :raises RuntimeError: If the session is uninitialized.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session
