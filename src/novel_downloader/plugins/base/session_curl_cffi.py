#!/usr/bin/env python3
"""
novel_downloader.plugins.base.session_curl_cffi
-----------------------------------------------
"""

# mypy: disable-error-code=unused-ignore

import json
from pathlib import Path
from typing import Any, Unpack

from curl_cffi.requests import AsyncSession

from novel_downloader.plugins.base.response import BaseResponse
from novel_downloader.plugins.base.session_base import (
    BaseSession,
    GetRequestKwargs,
    PostRequestKwargs,
)


class CurlCffiSession(BaseSession):
    """Session backend using curl_cffi for browser-like HTTP requests."""

    _session: AsyncSession[Any] | None

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        if self._session:
            return

        self._session = AsyncSession(
            headers=self._headers,
            cookies=self._cookies,
            timeout=self._timeout,
            impersonate=self._impersonate,  # type: ignore[arg-type]
            verify=self._verify_ssl,
            proxy=self._proxy,
        )

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        if self._session is not None:
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
            kwargs.setdefault("verify", verify)  # type: ignore[typeddict-item]
        if allow_redirects is not None:
            kwargs.setdefault("allow_redirects", allow_redirects)  # type: ignore[typeddict-item]

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
        if verify is not None:
            kwargs.setdefault("verify", verify)  # type: ignore[typeddict-item]
        if allow_redirects is not None:
            kwargs.setdefault("allow_redirects", allow_redirects)  # type: ignore[typeddict-item]

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

        filename = filename or "curl_cffi.cookies"
        path = cookies_dir / filename
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return False

        cookies = {
            item["name"]: item["value"]
            for item in data
            if "name" in item and "value" in item
        }
        self._session.cookies.update(cookies)
        return True

    def save_cookies(self, cookies_dir: Path, filename: str | None = None) -> bool:
        if self._session is None:
            return False

        filename = filename or "curl_cffi.cookies"
        cookies_dir.mkdir(parents=True, exist_ok=True)

        cookies: list[dict[str, str]] = []
        for name, value in self._session.cookies.items():
            cookies.append({"name": name, "value": value})

        (cookies_dir / filename).write_text(
            json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    def update_cookies(self, cookies: dict[str, str]) -> None:
        if self._session is None:
            return
        self._session.cookies.update(cookies)

    def get_cookie(self, key: str) -> str | None:
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
    def session(self) -> AsyncSession[Any]:
        """
        Return the active AsyncSession.

        :raises RuntimeError: If the session is uninitialized.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session
