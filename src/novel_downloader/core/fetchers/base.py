#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.base
-----------------------------------

Abstract base class providing common HTTP session handling for fetchers.
"""

import abc
import json
import logging
import types
from collections.abc import Mapping
from typing import Any, Self

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import FetcherConfig, LoginField
from novel_downloader.utils import (
    async_jitter_sleep,
)
from novel_downloader.utils.constants import (
    DATA_DIR,
    DEFAULT_USER_HEADERS,
)

from .rate_limiter import TokenBucketRateLimiter


class BaseSession(FetcherProtocol, abc.ABC):
    """
    BaseSession wraps basic HTTP operations using aiohttp.ClientSession.
    """

    def __init__(
        self,
        site: str,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async session with configuration.

        :param config: Configuration object for session behavior
        :param cookies: Optional initial cookies to set on the session.
        """
        self._site = site
        self._config = config

        self._state_file = DATA_DIR / site / "session_state.cookies"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        self._is_logged_in = False
        self._headers = (
            config.headers.copy() if config.headers else DEFAULT_USER_HEADERS.copy()
        )
        if config.user_agent:
            self._headers["User-Agent"] = config.user_agent
        self._cookies = cookies or {}
        self._session: ClientSession | None = None
        self._rate_limiter: TokenBucketRateLimiter | None = None

        if config.max_rps > 0:
            self._rate_limiter = TokenBucketRateLimiter(config.max_rps)

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

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

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.
        Subclasses that support user login/bookcase should override this.

        :return: The HTML of the bookcase page.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this session type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Set up the aiohttp.ClientSession with timeout, connector, headers.
        """
        timeout = ClientTimeout(total=self.timeout)
        connector = TCPConnector(
            ssl=self._config.verify_ssl,
            limit_per_host=self.max_connections,
        )
        self._session = ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self._headers,
            cookies=self._cookies,
        )

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

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

        for attempt in range(self.retry_times + 1):
            try:
                async with self.session.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    return await self._response_to_str(resp, encoding)
            except aiohttp.ClientError:
                if attempt < self.retry_times:
                    await async_jitter_sleep(
                        self.backoff_factor,
                        mul_spread=1.1,
                        max_sleep=self.backoff_factor + 2,
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
        self._cookies.update(cookies)
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
    def site(self) -> str:
        return self._site

    @property
    def is_logged_in(self) -> bool:
        """
        Indicates whether the requester is currently authenticated.
        """
        return self._is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return []

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
    def backoff_factor(self) -> float:
        return self._config.backoff_factor

    @property
    def retry_times(self) -> int:
        return self._config.retry_times

    @property
    def request_interval(self) -> float:
        return self._config.request_interval

    @property
    def timeout(self) -> float:
        return self._config.timeout

    @property
    def max_connections(self) -> int:
        return self._config.max_connections

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
