#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.base_session
---------------------------------------------

This module defines the BaseSession class, which provides basic HTTP
request capabilities using the requests library. It maintains a
persistent session and supports retries, headers, and timeout configurations.
"""

import abc
from typing import Any, Dict, Optional, Union

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter, Retry

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.interfaces import RequesterProtocol
from novel_downloader.utils.constants import DEFAULT_USER_HEADERS


class BaseSession(RequesterProtocol, abc.ABC):
    """
    BaseSession wraps basic HTTP operations using requests.Session,
    supporting retry logic, timeout, and persistent connections.

    Attributes:
        _session (requests.Session): The persistent HTTP session.
        _timeout (int): Timeout for each request in seconds.
    """

    def _init_session(
        self, config: RequesterConfig, cookies: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize the requests.Session with default headers and retry strategy.

        :param config: Configuration object for session behavior
                        (timeouts, retries, headers, etc.)
        """
        self._config = config
        self._timeout = config.timeout
        self._retry_times = config.retry_times
        self._retry_interval = config.retry_interval
        self._cookies = cookies or {}
        self._headers = DEFAULT_USER_HEADERS
        self._session: Optional[Session] = None

        self._setup()

    def _setup(self) -> None:
        """
        Set up the session with retry strategy and apply default headers.
        """
        self._session = requests.Session()

        retry_strategy = Retry(
            total=self._config.retry_times,
            backoff_factor=self._config.retry_interval,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update(self._headers)

        if self._cookies:
            self._session.cookies.update(self._cookies)

    def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Attempt to log in
        """
        raise NotImplementedError(
            "Login is not supported by this session type. "
            "Override login() in your subclass to enable it."
        )

    @abc.abstractmethod
    def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML (or JSON) of the book info page.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        """
        ...

    @abc.abstractmethod
    def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the raw HTML (or JSON) of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        """
        ...

    def get_bookcase(self, wait_time: Optional[int] = None) -> str:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.

        Subclasses that support user login and bookcase retrieval should override this.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML markup of the bookcase page.
        :raises NotImplementedError: If the subclass does not implement.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this session type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    def get(
        self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Response:
        """
        Send a GET request.

        :param url: The target URL.
        :param params: Query parameters to include in the request.
        :param kwargs: Additional arguments passed to requests.
        :return: Response object from the GET request.
        :raises RuntimeError: If the session is not initialized.
        """
        if not self._session:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session.get(url, params=params, timeout=self._timeout, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
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
        if not self._session:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session.post(
            url, data=data, json=json, timeout=self._timeout, **kwargs
        )

    @property
    def session(self) -> Session:
        """
        Return the active requests.Session.

        :raises RuntimeError: If the session is uninitialized or has been shut down.
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

    @property
    def headers(self) -> Dict[str, str]:
        """Return the default headers."""
        if not self._session:
            return {}
        return {k: v for k, v in self._session.headers.items() if isinstance(v, str)}

    def update_cookies(self, cookies: Dict[str, str], overwrite: bool = True) -> None:
        """
        Update cookies for the current session (if initialized) as well as for the
        internal cache kept in ``self._cookies`` so that subsequent ``_setup`` calls
        also see the latest values.
        """
        if not cookies:
            return

        if overwrite:
            for k, v in cookies.items():
                self._cookies[str(k)] = str(v)
        else:
            for k, v in cookies.items():
                self._cookies.setdefault(str(k), str(v))

        if self._session is not None:
            self._session.cookies.update(self._cookies)

    def shutdown(self) -> None:
        """
        Shutdown and clean up the session.

        This closes the underlying connection pool and removes the session.
        """
        if self._session:
            self._session.close()
            self._session = None

    def __getstate__(self) -> Dict[str, Any]:
        """
        Prepare object state for serialization.

        Removes unpickleable session object.

        :return: Serializable dict of the object state.
        """
        state = self.__dict__.copy()
        state.pop("_session", None)
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Restore object state and reinitialize session.

        :param state: Saved state dictionary.
        """
        self.__dict__.update(state)
        self._setup()
