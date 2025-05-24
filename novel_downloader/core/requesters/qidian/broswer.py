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
from novel_downloader.utils.i18n import t


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
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in to Qidian
        """
        if manual_login:
            return self._login_manual()
        else:
            return self._login_auto()

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

    def _login_auto(self, timeout: float = 5.0) -> bool:
        """
        Attempt to log in to Qidian by handling overlays and clicking the login button.

        :return: True if login succeeds or is already in place; False otherwise.
        """
        try:
            self.page.get("https://www.qidian.com/")
            self.page.wait.eles_loaded("#login-box", timeout=timeout)
        except Exception as e:
            self.logger.warning("[auth] Failed to load login box: %s", e)
            return False

        for attempt in range(1, self._retry_times + 1):
            if self._check_login_status():
                self.logger.debug("[auth] Already logged in.")
                break
            self.logger.debug("[auth] Attempting login click (#%s).", attempt)
            if self.click_button("@id=login-btn", timeout=timeout):
                self.logger.debug("[auth] Login button clicked.")
            else:
                self.logger.debug("[auth] Login button not found.")
            time.sleep(self._retry_interval)

        self._logged_in = self._check_login_status()
        if self._logged_in:
            self.logger.info("[auth] Login successful.")
        else:
            self.logger.warning("[auth] Login failed after max retries.")

        return self._logged_in

    def _login_manual(self) -> bool:
        """
        Guide the user through an interactive manual login flow.

        Steps:
            1. If the browser is headless, shut it down and restart in headful mode.
            2. Navigate to the Qidian homepage.
            3. Prompt the user to complete login, retrying up to `max_retries` times.
            4. Once logged in, restore original headless mode if needed.

        :param max_retries: Number of times to check for login success.
        :return: True if login was detected, False otherwise.
        """
        original_headless = self._headless

        # 1. Switch to headful mode if needed
        if self._disable_images_orig:
            self.logger.debug("[auth] Temporarily enabling images for manual login.")
            self._options.no_imgs(False)
            self.restart_browser(headless=False)
        elif original_headless:
            self.restart_browser(headless=False)

        # 2. Navigate to home page
        try:
            self.page.get("https://www.qidian.com/")
        except Exception as e:
            self.logger.warning(
                "[auth] Failed to load homepage for manual login: %s", e
            )
            return False

        # 3. Retry loop
        for attempt in range(1, self._retry_times + 1):
            if self._check_login_status():
                self.logger.debug("[auth] Already logged in.")
                self._logged_in = True
                break
            if attempt == 1:
                print(t("login_prompt_intro"))
            input(
                t(
                    "login_prompt_press_enter",
                    attempt=attempt,
                    max_retries=self._retry_times,
                )
            )
        else:
            self.logger.warning(
                "[auth] Manual login failed after %d attempts.", self._retry_times
            )
            self._logged_in = False
            return self._logged_in

        # 4. Restore headless if changed, then re-establish session
        if original_headless or self._disable_images_orig:
            self.logger.debug("[auth] Restoring browser settings after manual login...")
            self._options.no_imgs(self._disable_images_orig)
            self.restart_browser(headless=original_headless)
            self._logged_in = self._login_auto()
            if self._logged_in:
                self.logger.info(
                    "[auth] Login session successfully carried over after restart."
                )
            else:
                self.logger.warning(
                    "[auth] Lost login session after restoring headless mode."
                )

        return self._logged_in

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
