#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.qidian_requester.qidian_session
----------------------------------------------------------------

This module defines the QidianRequester class for interacting with
the Qidian website.
It extends the BaseSession by adding methods for logging in and
retrieving book information.
"""

from __future__ import annotations

import base64
import logging
import time
from typing import Any, Dict, Optional

from requests import Response

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base_session import BaseSession
from novel_downloader.utils.crypto_utils import patch_qd_payload_token
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import sleep_with_random_delay

logger = logging.getLogger(__name__)


class QidianSession(BaseSession):
    """
    A concrete :class:`BaseSession` for the Qidian site.  Besides the usual
    ``get``/``post`` helpers provided by the base class, this subclass adds:

    * URL builders for book info / chapter / bookcase pages
    * High-level convenience wrappers that:
        1. sleep a configurable (jittered) amount of time;
        2. retry on failures;
        3. automatically persist fresh cookies to :pydata:`state_mgr`
           so that the next run can reuse them.
    """

    DEFAULT_SCHEME = "https:"
    QIDIAN_BASE_URL = "www.qidian.com"
    QIDIAN_BOOKCASE_URL = f"{DEFAULT_SCHEME}//my.qidian.com/bookcase/"
    QIDIAN_BOOK_INFO_URL_1 = f"{DEFAULT_SCHEME}//www.qidian.com/book"
    QIDIAN_BOOK_INFO_URL_2 = f"{DEFAULT_SCHEME}//book.qidian.com/info"
    QIDIAN_CHAPTER_URL = f"{DEFAULT_SCHEME}//www.qidian.com/chapter"

    def __init__(self, config: RequesterConfig):
        """
        Initialise the underlying :class:`requests.Session`.
        """
        self._init_session(config=config)

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        """
        Same as :py:meth:`BaseSession.get`, but transparently refreshes
        a cookie-based token used for request validation.

        The method:
        1. Reads the existing cookie (if any);
        2. Generates a new value tied to *url*;
        3. Updates both the live ``requests.Session`` and the internal cache;
        4. Delegates the actual request to ``super().get``.
        """
        if self._session is None:  # defensive – mirrors BaseSession check
            raise RuntimeError("Session is not initialized or has been shut down.")

        # ---- 1. refresh token cookie --------------------------------------
        cookie_key = base64.b64decode("d190c2Zw").decode()
        old_token = self._session.cookies.get(cookie_key, "")

        if old_token:
            refreshed_token = patch_qd_payload_token(old_token, url)
            self._session.cookies.set(cookie_key, refreshed_token)
            self._cookies[cookie_key] = refreshed_token

        # ---- 2. perform the real GET --------------------------------------------
        resp: Response = super().get(url, params=params, **kwargs)

        # ---- 3. persist any server-set cookies (optional) --------------
        self.update_cookies(self._session.cookies.get_dict(), overwrite=True)
        state_mgr.set_cookies("qidian", self._cookies)

        return resp

    def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Restore cookies persisted by the browser-based workflow.
        """
        cookies: Dict[str, str] = state_mgr.get_cookies("qidian")
        if not cookies:
            logger.info(
                "[session] No stored cookies found: session remains unauthenticated."
            )
            return False

        # Merge cookies into both the internal cache and the live session
        self.update_cookies(cookies, overwrite=True)
        logger.info("[session] Loaded %d cookie(s) from state.", len(cookies))
        self.get("https://www.qidian.com")
        return True

    def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML of the book info page.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        """
        url = f"{self.QIDIAN_BOOK_INFO_URL_2}/{book_id}/"
        base_delay = wait_time or self._config.wait_time

        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.get(url)
                resp.raise_for_status()
                sleep_with_random_delay(base_delay, base_delay * 0.2)
                return resp.text
            except Exception as exc:
                logger.warning(
                    "[session] get_book_info(%s) attempt %s/%s failed: %s",
                    book_id,
                    attempt,
                    self.retry_times,
                    exc,
                )
                if attempt == self.retry_times:
                    raise
                time.sleep(self.retry_interval)

        raise RuntimeError("Unexpected fall-through in get_book_info")

    def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the HTML of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        """
        url = f"{self.QIDIAN_CHAPTER_URL}/{book_id}/{chapter_id}/"
        base_delay = wait_time or self._config.wait_time

        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.get(url)
                resp.raise_for_status()
                sleep_with_random_delay(base_delay, base_delay * 0.2)
                return resp.text
            except Exception as exc:
                logger.warning(
                    "[session] get_book_chapter(%s, %s) attempt %s/%s failed: %s",
                    book_id,
                    chapter_id,
                    attempt,
                    self.retry_times,
                    exc,
                )
                if attempt == self.retry_times:
                    raise
                time.sleep(self.retry_interval)

        raise RuntimeError("Unexpected fall-through in get_book_chapter")

    def get_bookcase(self, wait_time: Optional[int] = None) -> str:
        """
        Retrieve the user's *bookcase* page.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML markup of the bookcase page.
        """
        base_delay = wait_time or self._config.wait_time
        for attempt in range(1, self.retry_times + 1):
            try:
                resp = self.get(self.QIDIAN_BOOKCASE_URL, allow_redirects=True)
                resp.raise_for_status()
                sleep_with_random_delay(base_delay, base_delay * 0.2)
                return resp.text
            except Exception as exc:
                logger.warning(
                    "[session] get_bookcase attempt %s/%s failed: %s",
                    attempt,
                    self.retry_times,
                    exc,
                )
                if attempt == self.retry_times:
                    raise
                time.sleep(self.retry_interval)

        raise RuntimeError("Unexpected fall-through in get_bookcase")
