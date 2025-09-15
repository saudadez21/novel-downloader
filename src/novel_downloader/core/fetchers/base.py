#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.base
-----------------------------------

Abstract base class providing common HTTP session handling for fetchers.
"""

import abc
import asyncio
import json
import logging
import types
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Self
from urllib.parse import unquote, urlparse

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from novel_downloader.models import FetcherConfig, LoginField
from novel_downloader.utils import async_jitter_sleep, sanitize_filename
from novel_downloader.utils.constants import (
    DATA_DIR,
    DEFAULT_IMAGE_SUFFIX,
    DEFAULT_USER_HEADERS,
)
from novel_downloader.utils.file_utils.io import _unique_path, write_file

from .rate_limiter import TokenBucketRateLimiter


class BaseSession(abc.ABC):
    """
    BaseSession wraps basic HTTP operations using aiohttp.ClientSession.
    """

    site_name: str
    BASE_URL_MAP: dict[str, str] = {}
    DEFAULT_BASE_URL: str = ""

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async session with configuration.

        :param config: Configuration object for session behavior
        :param cookies: Optional initial cookies to set on the session.
        """
        self._base_url = self._resolve_base_url(config.locale_style)
        self._backoff_factor = config.backoff_factor
        self._request_interval = config.request_interval
        self._retry_times = config.retry_times
        self._timeout = config.timeout
        self._max_connections = config.max_connections
        self._verify_ssl = config.verify_ssl
        self._init_cookies = cookies or {}
        self._is_logged_in = False

        self._state_file = DATA_DIR / self.site_name / "session_state.cookies"

        self._headers = (
            config.headers.copy()
            if config.headers is not None
            else DEFAULT_USER_HEADERS.copy()
        )
        if config.user_agent:
            self._headers["User-Agent"] = config.user_agent

        self._session: ClientSession | None = None
        self._rate_limiter: TokenBucketRateLimiter | None = (
            TokenBucketRateLimiter(config.max_rps) if config.max_rps > 0 else None
        )

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Set up the aiohttp.ClientSession with timeout, connector, headers.
        """
        timeout = ClientTimeout(total=self._timeout)
        connector = TCPConnector(
            ssl=self._verify_ssl,
            limit_per_host=self._max_connections,
        )
        self._session = ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._headers,
            cookies=self._init_cookies,
        )

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
        """
        return False

    @abc.abstractmethod
    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        ...

    @abc.abstractmethod
    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        ...

    async def download_images(
        self,
        img_dir: Path,
        urls: list[str],
        batch_size: int = 10,
        *,
        on_exist: Literal["overwrite", "skip", "rename"] = "skip",
    ) -> None:
        """
        Download images to `img_dir` in batches.

        Any HTTP error (raise_for_status) is logged and skipped.

        :param img_dir: Destination folder.
        :param urls: List of image URLs (http/https).
        :param batch_size: Concurrency per batch.
        :param on_exist: What to do when file exists.
        """
        if not urls:
            return

        img_dir.mkdir(parents=True, exist_ok=True)

        for i in range(0, len(urls), max(1, batch_size)):
            batch = urls[i : i + batch_size]
            tasks = [
                self._download_one_image(url, img_dir, on_exist=on_exist)
                for url in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    self.logger.warning("Image download error: %s", r)

    @property
    def is_logged_in(self) -> bool:
        """
        Indicates whether the requester is currently authenticated.
        """
        return self._is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return []

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
                async with self.session.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    return await self._response_to_str(resp, encoding)
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

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """
        Send an HTTP GET request asynchronously.

        :param url: The target URL.
        :param params: Query parameters to include in the request.
        :param kwargs: Additional args passed to session.get().
        :return: aiohttp.ClientResponse object.
        :raises RuntimeError: If the session is not initialized.
        """
        return await self._request("GET", url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: dict[str, Any] | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """
        Send an HTTP POST request asynchronously.

        :param url: The target URL.
        :param data: Form data to include in the request body.
        :param json: JSON body to include in the request.
        :param kwargs: Additional args passed to session.post().
        :return: aiohttp.ClientResponse object.
        :raises RuntimeError: If the session is not initialized.
        """
        return await self._request("POST", url, data=data, json=json, **kwargs)

    async def load_state(self) -> bool:
        """
        Load session cookies from a file to restore previous login state.

        :return: True if the session state was loaded, False otherwise.
        """
        # if not self._state_file.exists() or self._session is None:
        #     return False
        # try:
        #     self._session.cookie_jar.load(self._state_file)
        #     self._is_logged_in = await self._check_login_status()
        #     return self._is_logged_in
        # except Exception as e:
        #     self.logger.warning("Failed to load state: %s", e)
        # return False
        if not self._state_file.exists() or self._session is None:
            return False
        try:
            storage = json.loads(self._state_file.read_text(encoding="utf-8"))
            raw_cookies = storage.get("cookies", [])
            cookie_dict = self._filter_cookies(raw_cookies)

            if cookie_dict:
                self._session.cookie_jar.update_cookies(cookie_dict)

            self._is_logged_in = await self._check_login_status()
            return self._is_logged_in
        except Exception as e:
            self.logger.warning("Failed to load state: %s", e)
            return False

    async def save_state(self) -> bool:
        """
        Save the current session cookies to a file for future reuse.

        :return: True if the session state was saved, False otherwise.
        """
        # if self._session is None:
        #     return False
        # try:
        #     self._session.cookie_jar.save(self._state_file)
        #     return True
        # except Exception as e:
        #     self.logger.warning("Failed to save state: %s", e)
        # return False
        if self._session is None:
            return False
        try:
            cookies = []
            for cookie in self._session.cookie_jar:
                cookies.append(
                    {
                        "name": cookie.key,
                        "value": cookie.value,
                    }
                )
            storage_state = {
                "cookies": cookies,
                "origins": [],
            }
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(storage_state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return True
        except Exception as e:
            self.logger.warning("Failed to save state: %s", e)
            return False

    def update_cookies(
        self,
        cookies: dict[str, str],
    ) -> None:
        """
        Update or add multiple cookies in the session.

        :param cookies: A dictionary of cookie key-value pairs.
        """
        if self._session:
            self._session.cookie_jar.update_cookies(cookies)

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> ClientResponse:
        if self._rate_limiter:
            await self._rate_limiter.wait()
        return await self.session.request(method, url, **kwargs)

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        return False

    @property
    def session(self) -> ClientSession:
        """
        Return the active aiohttp.ClientSession.

        :raises RuntimeError: If the session is uninitialized.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session

    async def _sleep(self) -> None:
        if self._request_interval > 0:
            await async_jitter_sleep(
                self._request_interval,
                mul_spread=1.1,
                max_sleep=self._request_interval + 2,
            )

    @property
    def headers(self) -> dict[str, str]:
        """
        Get a copy of the current session headers for temporary use.

        :return: A dict mapping header names to their values.
        """
        if self._session:
            return dict(self._session.headers)
        return self._headers.copy()

    @staticmethod
    def _filter_cookies(
        raw_cookies: list[Mapping[str, Any]],
    ) -> dict[str, str]:
        """
        Hook:
        take the raw list of cookie-dicts loaded from storage_state
        and return a simple name -> value mapping.
        """
        return {c["name"]: c["value"] for c in raw_cookies}

    @staticmethod
    async def _response_to_str(
        resp: ClientResponse,
        encoding: str | None = None,
    ) -> str:
        """
        Read the full body of resp as text. Try the provided encoding,
        response charset, and common fallbacks. On failure, fall back
        to utf-8 with errors ignored.
        """
        data: bytes = await resp.read()
        encodings: list[str | None] = [
            encoding,
            resp.charset,
            "gb2312",
            "gb18030",
            "gbk",
            "utf-8",
        ]

        for enc in (e for e in encodings if e is not None):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode(encoding or "utf-8", errors="ignore")

    async def _download_one_image(
        self,
        url: str,
        folder: Path,
        *,
        on_exist: Literal["overwrite", "skip", "rename"],
    ) -> None:
        """Download a single image."""
        async with self.session.get(url) as resp:
            save_path = self._build_filepath(
                url=url,
                folder=folder,
                default_suffix=DEFAULT_IMAGE_SUFFIX,
                on_exist=on_exist,
            )
            if save_path.exists() and on_exist == "skip":
                return

            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                self.logger.warning("Skip %s (HTTP %s): %s", url, e.status, e)
                return

            write_file(
                content=await resp.read(),  # bytes
                filepath=save_path,
                on_exist=on_exist,
            )
            self.logger.debug("Saved image: %s <- %s", save_path, url)

    def _resolve_base_url(self, locale_style: str) -> str:
        key = locale_style.strip().lower()
        return self.BASE_URL_MAP.get(key, self.DEFAULT_BASE_URL)

    @staticmethod
    def _build_filepath(
        url: str,
        folder: Path,
        default_suffix: str,
        on_exist: Literal["overwrite", "skip", "rename"],
    ) -> Path:
        parsed_url = urlparse(url)
        url_path = Path(unquote(parsed_url.path))

        raw_name = url_path.name or "unnamed"
        name = sanitize_filename(raw_name)

        if "." not in name and (url_path.suffix or default_suffix):
            name += url_path.suffix or default_suffix

        file_path = folder / name
        if on_exist == "rename":
            file_path = _unique_path(file_path)

        return file_path

    async def __aenter__(self) -> Self:
        if self._session is None or self._session.closed:
            await self.init()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        await self.close()
