#!/usr/bin/env python3
"""
novel_downloader.core.requesters.base.session
---------------------------------------------

This module defines the BaseSession class, which provides basic HTTP
request capabilities using the requests library. It maintains a
persistent session and supports retries, headers, and timeout configurations.
"""

import abc
import logging
import types
from collections.abc import Mapping
from typing import Any, Literal, Self

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.interfaces import SyncRequesterProtocol
from novel_downloader.utils.constants import DEFAULT_USER_HEADERS


class BaseSession(SyncRequesterProtocol, abc.ABC):
    """
    BaseSession wraps basic HTTP operations using requests.Session,
    supporting retry logic, timeout, and persistent connections.

    Attributes:
        _session (requests.Session): The persistent HTTP session.
    """

    def is_async(self) -> Literal[False]:
        return False

    def __init__(
        self,
        config: RequesterConfig,
        cookies: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize a Session instance.

        :param config: The RequesterConfig instance containing settings.
        :param cookies: Optional cookies to preload into the session.
        """
        super().__init__()
        self._config = config
        self._cookies = cookies or {}
        self._headers = DEFAULT_USER_HEADERS.copy()
        self._session: Session | None = None

        retry_strategy = Retry(
            total=config.retry_times,
            backoff_factor=config.backoff_factor,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        self._adapter = HTTPAdapter(max_retries=retry_strategy)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self._init_session()

    def _init_session(self) -> None:
        """
        Set up the session with retry strategy and apply default headers.
        """
        if self._session:
            return

        self._session = requests.Session()
        self._session.mount("http://", self._adapter)
        self._session.mount("https://", self._adapter)
        self._session.headers.update(self._headers)

        if self._cookies:
            self._session.cookies.update(self._cookies)

    def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in
        """
        return True

    @abc.abstractmethod
    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of the book info page.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        ...

    @abc.abstractmethod
    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        ...

    def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.

        Subclasses that support user login and bookcase retrieval should override this.

        :param page: Page idx
        :return: The HTML markup of the bookcase page.
        :raises NotImplementedError: If the subclass does not implement.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this session type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Send a GET request.

        :param url: The target URL.
        :param params: Query parameters to include in the request.
        :param kwargs: Additional arguments passed to requests.
        :return: Response object from the GET request.
        :raises RuntimeError: If the session is not initialized.
        """
        return self.session.get(url, params=params, **kwargs)

    def post(
        self,
        url: str,
        data: dict[str, Any] | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Send a POST request.

        :param url: The target URL.
        :param data: Form data to include in the request body.
        :param json: JSON body to include in the request.
        :param kwargs: Additional arguments passed to requests.
        :return: Response object from the POST request.
        :raises RuntimeError: If the session is not initialized.
        """
        return self.session.post(url, data=data, json=json, **kwargs)

    def put(
        self,
        url: str,
        data: dict[str, Any] | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Send a PUT request with retry logic.
        """
        return self.session.put(url, data=data, json=json, **kwargs)

    def patch(
        self,
        url: str,
        data: dict[str, Any] | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Send a PATCH request with retry logic.
        """
        return self.session.patch(url, data=data, json=json, **kwargs)

    def delete(
        self,
        url: str,
        **kwargs: Any,
    ) -> Response:
        """
        Send a DELETE request with retry logic.
        """
        return self.session.delete(url, **kwargs)

    @property
    def session(self) -> Session:
        """
        Return the active requests.Session.

        :raises RuntimeError: If the session is uninitialized or has been shut down.
        """
        if self._session is None:
            # self._init_session()
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session

    @property
    def cookies(self) -> dict[str, str]:
        """
        Get the current session cookies.

        :return: A dict mapping cookie names to their values.
        """
        if self._session:
            return self._session.cookies.get_dict()
        else:
            return self._cookies

    @property
    def headers(self) -> Mapping[str, str | bytes]:
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

    def del_header(self, key: str) -> None:
        """
        Delete a header from the session if it exists.

        :param key: The name of the header to remove.
        """
        self._headers.pop(key, None)
        if self._session:
            self._session.headers.pop(key, None)

    def update_cookie(self, key: str, value: str) -> None:
        """
        Update or add a single cookie in the session.

        :param key: The name of the cookie.
        :param value: The value of the cookie.
        """
        self._cookies[key] = value
        if self._session:
            self._session.cookies.set(key, value)

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
            self._session.cookies.update(cookies)

    def clear_cookies(self) -> None:
        """
        Clear cookies from the session.
        """
        self._cookies = {}
        if self._session:
            self._session.cookies.clear()

    def _on_close(self) -> None:
        """
        Hook method called at the beginning of close().
        Override in subclass if needed.
        """
        pass

    def close(self) -> None:
        """
        Shutdown and clean up the session.

        This closes the underlying connection pool and removes the session.
        """
        self._on_close()
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> Self:
        if self._session is None:
            self._init_session()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def __getstate__(self) -> dict[str, Any]:
        """
        Prepare object state for serialization.

        Removes unpickleable session object.

        :return: Serializable dict of the object state.
        """
        self.close()
        state = self.__dict__.copy()
        state.pop("_session", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Restore object state and reinitialize session.

        :param state: Saved state dictionary.
        """
        self.__dict__.update(state)
        self._init_session()
