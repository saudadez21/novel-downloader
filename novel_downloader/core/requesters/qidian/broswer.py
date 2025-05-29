#!/usr/bin/env python3
"""
novel_downloader.core.requesters.qidian.broswer
-----------------------------------------------

This module defines the QidianRequester class for interacting with
the Qidian website.
It extends the BaseBrowser by adding methods for logging in and
retrieving book information.
"""

import time
from typing import Any

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base import BaseBrowser


class QidianBrowser(BaseBrowser):
    """
    QidianRequester provides methods for interacting with Qidian.com,
    including checking login status and preparing book-related URLs.

    Inherits base browser setup from BaseBrowser.
    """

    BOOKCASE_URL = "https://my.qidian.com/bookcase/"
    BOOK_INFO_URL = "https://book.qidian.com/info/{book_id}/"
    CHAPTER_URL = "https://www.qidian.com/chapter/{book_id}/{chapter_id}/"

    def __init__(
        self,
        config: RequesterConfig,
    ):
        """
        Initialize the QidianRequester with a browser configuration.

        :param config: The RequesterConfig instance containing browser settings.
        """
        super().__init__(config)
        self._logged_in: bool = False
        self._retry_times = config.retry_times
        self._retry_interval = config.backoff_factor
        self._timeout = config.timeout

    def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in to Qidian via auto interaction.

        :param attempt: Number of login attempts.
        :param retry_interval: Seconds to wait between retries.
        :return: True if login succeeded, False otherwise.
        """
        for i in range(attempt):
            if self._login_auto():
                self._logged_in = True
                return True

            self.logger.debug("[auth] Login attempt %d failed, retrying...", i + 1)
            if i < attempt - 1:
                time.sleep(self._retry_interval)

        self._logged_in = False
        self.logger.warning("[auth] Login failed after %d attempts.", attempt)
        return False

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the HTML of a Qidian book info page.

        :param book_id: The identifier of the book to fetch.
        :return: The HTML content of the book info page, or an empty string on error.
        """
        url = self.book_info_url(book_id)
        try:
            # Navigate and fetch
            self.page.get(url)
            html = str(self.page.html)
            self.logger.debug(
                "[fetch] Fetched book info for ID %s from %s", book_id, url
            )
            return [html]
        except Exception as e:
            self.logger.warning(
                "[fetch] Error fetching book info from '%s': %s", url, e
            )
        return []

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the HTML content of a specific chapter.

        Ensures the user is logged in, navigates to the chapter page

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: The HTML content of the chapter page, or empty string on error.
        """
        url = self.chapter_url(book_id, chapter_id)
        try:
            # Navigate to chapter URL
            self.page.get(url)
            html = str(self.page.html)
            self.logger.debug(
                "[fetch] Fetched chapter %s for book %s", chapter_id, book_id
            )
            return [html]
        except Exception as e:
            self.logger.warning("[fetch] Error fetching chapter from '%s': %s", url, e)
        return []

    def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the HTML content of the logged-in user's Qidian bookcase page.

        :return: The HTML markup of the bookcase page, or empty string on error.
        :raises RuntimeError: If the user is not logged in.
        """
        if not self._logged_in:
            raise RuntimeError("User not logged in. Please call login() first.")

        url = self.bookcase_url()
        try:
            # Navigate to the bookcase page
            self.page.get(url)
            html = str(self.page.html)
            self.logger.debug("[fetch] Fetched bookcase HTML from %s", url)
            return [html]
        except Exception as e:
            self.logger.warning("[fetch] Error fetching bookcase from '%s': %s", url, e)
        return []

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)

    @classmethod
    def bookcase_url(cls) -> str:
        """
        Construct the URL for the user's bookcase page.

        :return: Fully qualified URL of the bookcase.
        """
        return cls.BOOKCASE_URL

    def set_interactive_mode(self, enable: bool) -> bool:
        """
        Enable or disable interactive browser mode for manual login.

        When enabled, restarts browser in headful mode with images.
        When disabled, restores browser to original state and checks login.

        :param enable: True to enable, False to disable interactive mode.
        :return: True if operation or login check succeeded, False otherwise.
        """
        if enable:
            if self._disable_images_orig:
                self._options.no_imgs(False)
            if self._headless_orig or self._disable_images_orig:
                self.restart_browser(headless=False)
            self.page.get("https://www.qidian.com/")
            return True

        # restore
        if self._disable_images_orig or self._headless_orig:
            self._options.no_imgs(self._disable_images_orig)
            self.restart_browser(headless=self._headless_orig)

            success = self._check_login_status()
            self._logged_in = success

            if success:
                self._logged_in = self._login_auto()

        return self._logged_in

    def _login_auto(self, timeout: float = 5.0) -> bool:
        """
        Attempt one automatic login interaction (click once and check).

        :param timeout: Seconds to wait for login box to appear.
        :return: True if login successful or already logged in; False otherwise.
        """
        try:
            self.page.get("https://www.qidian.com/")
            self.page.wait.eles_loaded("#login-box", timeout=timeout)
        except Exception as e:
            self.logger.warning("[auth] Failed to load login box: %s", e)
            return False

        if self._check_login_status():
            self.logger.debug("[auth] Already logged in.")
            return True

        self.logger.debug("[auth] Clicking login button once.")
        self.click_button("@id=login-btn", timeout=timeout)

        return self._check_login_status()

    def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by inspecting
        the visibility of the 'sign-in' element on the page.

        :return: True if the user appears to be logged in, False otherwise.
        """
        try:
            self._dismiss_overlay()
            sign_in_elem = self.page.ele("@class=sign-in")
            if sign_in_elem:
                class_value = sign_in_elem.attr("class")
                if class_value and "hidden" not in class_value:
                    return True
        except Exception as e:
            self.logger.warning("[auth] Error while checking login status: %s", e)
        return False

    def _dismiss_overlay(self, timeout: float = 2.0) -> None:
        """
        Detect and close any full-page overlay mask that might block the login UI.
        """
        try:
            mask = self.page.ele("@@tag()=div@@class=mask", timeout=timeout)
            if not mask:
                return
            self.logger.debug("[auth] Overlay mask detected; attempting to close.")
            iframe = self.get_frame("loginIfr")
            if iframe is None:
                self.logger.debug("[auth] Login iframe not found.")
                return
            self.click_button("@id=close", page=iframe)
        except Exception as e:
            self.logger.debug("[auth] Error handling overlay mask: %s", e)
