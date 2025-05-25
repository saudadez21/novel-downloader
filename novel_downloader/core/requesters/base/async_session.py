#!/usr/bin/env python3
"""
novel_downloader.core.requesters.base.async_session
---------------------------------------------------

This module defines the BaseAsyncSession class, which provides asynchronous
HTTP request capabilities using aiohttp. It maintains a persistent
client session and supports retries, headers, timeout configurations,
cookie handling, and defines abstract methods for subclasses.
"""

import abc
import asyncio
import logging
import random
import time
import types
from typing import Any, Literal, Self

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.interfaces import AsyncRequesterProtocol
from novel_downloader.utils.constants import DEFAULT_USER_HEADERS


class RateLimiter:
    """
    Simple async token-bucket rate limiter:
    ensures no more than rate_per_sec
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
                jitter = random.uniform(0, 0.3)
                await asyncio.sleep(delay + jitter)
            self._last = time.monotonic()


class BaseAsyncSession(AsyncRequesterProtocol, abc.ABC):
    """
    BaseAsyncSession wraps basic HTTP operations using aiohttp.ClientSession,
    supporting retry logic, timeout, persistent connections, and cookie management.

    Attributes:
        _session (ClientSession): The persistent aiohttp client session.
        _timeout (float): Timeout for each request in seconds.
        _retry_times (int): Number of retry attempts on failure.
        _retry_interval (float): Delay (in seconds) between retries.
        _headers (Dict[str, str]): Default HTTP headers to send.
        _cookies (Dict[str, str]): Optional cookie jar for the session.
    """

    def is_async(self) -> Literal[True]:
        return True

    def __init__(
        self,
        config: RequesterConfig,
        cookies: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the async session with configuration.

        :param config: Configuration object for session behavior
                       (timeouts, retries, headers, etc.)
        :param cookies: Optional initial cookies to set on the session.
        """
        self._config = config
        self._retry_times = config.retry_times
        self._retry_interval = config.backoff_factor
        self._timeout = config.timeout
        self._max_rps = config.max_rps
        self._max_connections = config.max_connections

        self._cookies = cookies or {}
        self._headers = DEFAULT_USER_HEADERS.copy()
        self._session: ClientSession | None = None
        self._rate_limiter: RateLimiter | None = None

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self._init_session()

    def _init_session(self) -> None:
        """
        Set up the aiohttp.ClientSession with timeout, connector, headers, and cookies.
        """
        if self._max_rps is not None:
            self._rate_limiter = RateLimiter(self._max_rps)

        timeout = ClientTimeout(total=self._timeout)
        connector = TCPConnector(limit_per_host=self._max_connections)
        self._session = ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._headers,
            cookies=self._cookies,
        )

    async def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.
        Override in subclasses that require authentication.

        :returns: True if login succeeded, False otherwise.
        """
        return True

    @abc.abstractmethod
    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
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
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        """
        ...

    async def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
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
        if self._rate_limiter:
            await self._rate_limiter.wait()

        for attempt in range(self._retry_times + 1):
            try:
                async with self.session.get(url, **kwargs) as resp:
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
    def cookies(self) -> dict[str, str]:
        """
        Get the current session cookies.

        :return: A dict mapping cookie names to their values.
        """
        if self._session:
            return {c.key: c.value for c in self._session.cookie_jar}
        else:
            return self._cookies

    @property
    def headers(self) -> dict[str, str]:
        """
        Get a copy of the current session headers for temporary use.

        :return: A dict mapping header names to their values.
        """
        if self._session:
            return dict(self._session.headers)
        return self._headers.copy()

    def get_header(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific header value by name.

        :param key: The header name to look up.
        :param default: The value to return if the header is not present.
        :return: The header value if present, else default.
        """
        if self._session:
            return self._session.headers.get(key, default)
        else:
            return self._headers.get(key, default)

    def update_header(self, key: str, value: str) -> None:
        """
        Update or add a single header in the session.

        :param key: The name of the header.
        :param value: The value of the header.
        """
        self._headers[key] = value
        if self._session:
            self._session.headers[key] = value

    def update_headers(self, headers: dict[str, str]) -> None:
        """
        Update or add multiple headers in the session.

        :param headers: A dictionary of header key-value pairs.
        """
        self._headers.update(headers)
        if self._session:
            self._session.headers.update(headers)

    def update_cookie(self, key: str, value: str) -> None:
        """
        Update or add a single cookie in the session.

        :param key: The name of the cookie.
        :param value: The value of the cookie.
        """
        self._cookies[key] = value
        if self._session:
            self._session.cookie_jar.update_cookies({key: value})

    def update_cookies(
        self,
        cookies: dict[str, str],
    ) -> None:
        """
        Update or add multiple cookies in the session.

        :param cookies: A dictionary of cookie key-value pairs.
        """
        self._cookies.update(cookies)
        if self._session:
            self._session.cookie_jar.update_cookies(cookies)

    def clear_cookies(self) -> None:
        """
        Clear cookies from the session.
        """
        self._cookies = {}
        if self._session:
            self._session.cookie_jar.clear()

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> ClientResponse:
        if self._rate_limiter:
            await self._rate_limiter.wait()
        return await self.session.request(method, url, **kwargs)

    async def _on_close(self) -> None:
        """
        Async hook method called before closing.
        Override in subclass.
        """
        pass

    async def close(self) -> None:
        """
        Shutdown and clean up the session. Closes connection pool.
        """
        await self._on_close()
        if self._session:
            await self._session.close()
            self._session = None

    def sync_close(self) -> None:
        """
        Sync wrapper for closing the aiohttp session
        when called from sync contexts.
        """
        if self._session:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.close())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.close())
                loop.close()

    async def __aenter__(self) -> Self:
        if self._session is None:
            self._init_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        await self.close()

    def __del__(self) -> None:
        self.sync_close()

    def __getstate__(self) -> dict[str, Any]:
        """
        Prepare object state for serialization: remove unpickleable session.
        """
        self.sync_close()
        state = self.__dict__.copy()
        state.pop("_session", None)
        state.pop("_rate_limiter", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Restore object state. Session will be lazily reinitialized on next request.
        """
        self.__dict__.update(state)
        self._session = None
