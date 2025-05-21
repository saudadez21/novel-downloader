#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.biquge.session
-----------------------------------------------

"""

import time
from typing import Dict, Optional

from novel_downloader.config import RequesterConfig
from novel_downloader.core.requesters.base import BaseSession
from novel_downloader.utils.time_utils import sleep_with_random_delay


class BiqugeSession(BaseSession):
    """
    A session class for interacting with the Biquge (www.b520.cc) novel website.
    """

    BOOK_INFO_URL = "http://www.b520.cc/{book_id}/"
    CHAPTER_URL = "http://www.b520.cc/{book_id}/{chapter_id}.html"

    def __init__(
        self,
        config: RequesterConfig,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Biquge session with configuration and optional cookies.

        :param config: The requester configuration.
        :param cookies: Optional dictionary of cookies to be used in the session.
        """
        self._init_session(config=config, cookies=cookies)

    def get_book_info(self, book_id: str, wait_time: Optional[float] = None) -> str:
        """
        Fetch the raw HTML (or JSON) of the book info page.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        :raises requests.HTTPError: If the request returns an unsuccessful status code.
        """
        url = self.book_info_url(book_id=book_id)
        base = wait_time if wait_time is not None else self._config.wait_time

        for attempt in range(1, self.retry_times + 1):
            try:
                with self.session.get(url, timeout=self.timeout) as response:
                    response.raise_for_status()
                    content = response.text
                sleep_with_random_delay(base, add_spread=1.0)
                return content
            except Exception as e:
                if attempt == self.retry_times:
                    raise e
                else:
                    time.sleep(self.retry_interval)
                    continue
        raise RuntimeError("Unexpected error: get_book_info failed without returning")

    def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[float] = None
    ) -> str:
        """
        Fetch the raw HTML (or JSON) of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        :raises requests.HTTPError: If the request returns an unsuccessful status code.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        base = wait_time if wait_time is not None else self._config.wait_time

        for attempt in range(1, self.retry_times + 1):
            try:
                with self.session.get(url, timeout=self.timeout) as response:
                    response.raise_for_status()
                    content = response.text
                sleep_with_random_delay(base, add_spread=1.0)
                return content
            except Exception as e:
                if attempt == self.retry_times:
                    raise e
                else:
                    time.sleep(self.retry_interval)
                    continue
        raise RuntimeError(
            "Unexpected error: get_book_chapter failed without returning"
        )

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for the book's main information page.

        :param book_id: The unique identifier of the book.
        :return: Fully formatted URL string pointing to the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for a specific chapter of a book.

        :param book_id: The unique identifier of the book.
        :param chapter_id: The identifier of the chapter within the book.
        :return: Fully formatted URL string pointing to the chapter page.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
