#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.base_async_session
---------------------------------------------------

This module defines the BaseAsyncSession class, which provides asynchronous
HTTP request capabilities using aiohttp. It maintains a persistent
client session and supports retries, headers, timeout configurations,
cookie handling, and defines abstract methods for subclasses.
"""

import abc
import asyncio
import time
from typing import Any, Dict, Optional, Union

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.interfaces import AsyncRequesterProtocol
from novel_downloader.utils.constants import DEFAULT_USER_HEADERS


class RateLimiter:
    """
    Simple async token-bucket rate limiter: ensures no more than rate_per_sec
    requests are started per second, across all coroutines.
    """

    def __init__(self, rate_per_sec: float):
        self._interval = 1.0 / rate_per_sec
        self._lock = asyncio.Lock()
        self._last = time.monotonic()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            delay = self._interval - elapsed
            if delay > 0:
                await asyncio.sleep(delay)
            self._last = time.monotonic()


class BaseAsyncSession(AsyncRequesterProtocol, abc.ABC):
    """
    BaseAsyncSession wraps basic HTTP operations using aiohttp.ClientSession,
    supporting retry logic, timeout, persistent connections, and cookie management.

    Attributes:
        _session (ClientSession): The persistent aiohttp client session.
        _timeout (int): Timeout for each request in seconds.
        _retry_times (int): Number of retry attempts on failure.
        _retry_interval (float): Delay (in seconds) between retries.
        _headers (Dict[str, str]): Default HTTP headers to send.
        _cookies (Dict[str, str]): Optional cookie jar for the session.
    """

    def _init_session(
        self,
        config: RequesterConfig,
        cookies: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the async session with configuration.

        :param config: Configuration object for session behavior
                       (timeouts, retries, headers, etc.)
        :param cookies: Optional initial cookies to set on the session.
        """
        self._config = config
        self._timeout = config.timeout
        self._retry_times = config.retry_times
        self._retry_interval = config.retry_interval
        self._cookies = cookies or {}
        self._headers = DEFAULT_USER_HEADERS.copy()
        self._session: Optional[ClientSession] = None
        self._rate_limiter: Optional[RateLimiter] = None

    async def _setup(self) -> None:
        """
        Set up the aiohttp.ClientSession with timeout, connector, headers, and cookies.
        """
        max_rps = getattr(self._config, "max_rps", None)
        if max_rps is not None:
            self._rate_limiter = RateLimiter(max_rps)

        timeout = ClientTimeout(total=self._timeout)
        connector = TCPConnector(
            limit_per_host=getattr(self._config, "max_connections", 10)
        )
        self._session = ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._headers,
            cookies=self._cookies,
        )

    async def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Attempt to log in asynchronously.
        Override in subclasses that require authentication.

        :returns: True if login succeeded, False otherwise.
        """
        raise NotImplementedError(
            "Login is not supported by this session type. "
            "Override login() in your subclass to enable it."
        )

    @abc.abstractmethod
    async def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        """
        ...

    @abc.abstractmethod
    async def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the raw HTML (or JSON) of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        """
        ...

    async def get_bookcase(self, wait_time: Optional[int] = None) -> str:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.
        Subclasses that support user login/bookcase should override this.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML of the bookcase page.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this session type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    async def fetch(self, url: str, **kwargs: Any) -> str:
        """
        Fetch the content from the given URL asynchronously, with retry support.

        :param url: The target URL to fetch.
        :param kwargs: Additional keyword arguments to pass to `session.get`.
        :return: The response body as text.
        :raises: aiohttp.ClientError on final failure.
        """
        if self._session is None:
            await self._setup()
        if self._session is None:
            raise RuntimeError("Session not initialized after setup")

        if self._rate_limiter:
            await self._rate_limiter.wait()

        for attempt in range(self._retry_times + 1):
            try:
                async with self._session.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    text: str = await resp.text()
                    return text
            except aiohttp.ClientError:
                if attempt < self._retry_times:
                    await asyncio.sleep(self._retry_interval)
                    continue
                raise

        raise RuntimeError("Unreachable code reached in fetch()")

    async def get(
        self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> ClientResponse:
        """
        Send an HTTP GET request asynchronously.

        :param url: The target URL.
        :param params: Query parameters to include in the request.
        :param kwargs: Additional args passed to session.get().
        :return: aiohttp.ClientResponse object.
        :raises RuntimeError: If the session is not initialized.
        """
        if self._session is None:
            await self._setup()
        if self._session is None:
            raise RuntimeError("Session not initialized after setup")

        if self._rate_limiter:
            await self._rate_limiter.wait()
        return await self._session.get(url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
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
        if self._session is None:
            await self._setup()
        if self._session is None:
            raise RuntimeError("Session not initialized after setup")

        if self._rate_limiter:
            await self._rate_limiter.wait()
        return await self._session.post(url, data=data, json=json, **kwargs)

    @property
    def session(self) -> ClientSession:
        """
        Return the active aiohttp.ClientSession.

        :raises RuntimeError: If the session is uninitialized.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session

    @property
    def timeout(self) -> int:
        """Return the default timeout setting."""
        return self._timeout

    @property
    def retry_times(self) -> int:
        """Return the maximum number of retry attempts."""
        return self._retry_times

    @property
    def retry_interval(self) -> float:
        """Return the base interval (in seconds) between retries."""
        return self._retry_interval

    async def update_cookies(
        self, cookies: Dict[str, str], overwrite: bool = True
    ) -> None:
        """
        Update cookies for the current session and internal cache.

        :param cookies: New cookies to merge.
        :param overwrite: If True, replace existing; else, only set missing.
        """
        # update internal cache
        if overwrite:
            self._cookies.update({str(k): str(v) for k, v in cookies.items()})
        else:
            for k, v in cookies.items():
                self._cookies.setdefault(str(k), str(v))

        # apply to live session
        if self._session:
            self._session.cookie_jar.update_cookies(self._cookies)

    async def shutdown(self) -> None:
        """
        Shutdown and clean up the session. Closes connection pool.
        """
        if self._session:
            await self._session.close()
            self._session = None

    def __getstate__(self) -> Dict[str, Any]:
        """
        Prepare object state for serialization: remove unpickleable session.
        """
        state = self.__dict__.copy()
        state.pop("_session", None)
        state.pop("_rate_limiter", None)
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Restore object state. Session will be lazily reinitialized on next request.
        """
        self.__dict__.update(state)
        self._session = None
