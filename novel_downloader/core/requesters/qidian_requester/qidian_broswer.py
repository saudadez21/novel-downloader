#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.qidian_requester.qidian_broswer
----------------------------------------------------------------

This module defines the QidianRequester class for interacting with
the Qidian website.
It extends the BaseBrowser by adding methods for logging in and
retrieving book information.
"""

import logging
import random
import time
from typing import Optional

from DrissionPage.common import Keys

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base_browser import BaseBrowser
from novel_downloader.utils.time_utils import sleep_with_random_delay

logger = logging.getLogger(__name__)


class QidianBrowser(BaseBrowser):
    """
    QidianRequester provides methods for interacting with Qidian.com,
    including checking login status and preparing book-related URLs.

    Inherits base browser setup from BaseBrowser.
    """

    DEFAULT_SCHEME = "https:"
    QIDIAN_BASE_URL = "www.qidian.com"
    QIDIAN_BOOKCASE_URL = f"{DEFAULT_SCHEME}//my.qidian.com/bookcase/"
    QIDIAN_BOOK_INFO_URL_1 = f"{DEFAULT_SCHEME}//www.qidian.com/book"
    QIDIAN_BOOK_INFO_URL_2 = f"{DEFAULT_SCHEME}//book.qidian.com/info"
    QIDIAN_CHAPTER_URL = f"{DEFAULT_SCHEME}//www.qidian.com/chapter"

    def __init__(self, config: RequesterConfig):
        """
        Initialize the QidianRequester with a browser configuration.

        :param config: The RequesterConfig instance containing browser settings.
        """
        self._init_browser(config=config)
        self._headless: bool = config.headless
        self._logged_in: bool = False

    def _is_user_logged_in(self) -> bool:
        """
        Check whether the user is currently logged in by inspecting
        the visibility of the 'sign-in' element on the page.

        :return: True if the user appears to be logged in, False otherwise.
        """
        try:
            self._handle_overlay_mask()
            sign_in_elem = self._page.ele("@class=sign-in")
            if sign_in_elem:
                class_value = sign_in_elem.attr("class")
                if class_value and "hidden" not in class_value:
                    return True
        except Exception as e:
            logger.warning("[auth] Error while checking login status: %s", e)
        return False

    def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Attempt to log in to Qidian
        """
        if manual_login:
            return self._manual_login(max_retries)
        else:
            return self._login(max_retries)

    def _login(self, max_retries: int = 3) -> bool:
        """
        Attempt to log in to Qidian by handling overlays and clicking the login button.

        :param max_retries: Maximum number of times to try clicking the login button.
        :return: True if login succeeds or is already in place; False otherwise.
        """
        original_url = self._page.url
        try:
            self._page.get("https://www.qidian.com/")
            self._page.wait.eles_loaded("#login-box")
        except Exception as e:
            logger.warning("[auth] Failed to load login box: %s", e)
            return False

        for attempt in range(1, max_retries + 1):
            if self._is_user_logged_in():
                logger.debug("[auth] Already logged in.")
                break

            self._click_login_button(attempt)
            time.sleep(self._config.retry_interval)

        self._logged_in = self._is_user_logged_in()
        if self._logged_in:
            logger.info("[auth] Login successful.")
        else:
            logger.warning("[auth] Login failed after max retries.")

        # return to original page
        try:
            self._page.get(original_url)
        except Exception as e:
            logger.debug("[auth] Failed to restore page URL: %s", e)

        return self._logged_in

    def _handle_overlay_mask(self) -> None:
        """
        Detect and close any full-page overlay mask that might block the login UI.
        """
        try:
            mask = self._page.ele("@@tag()=div@@class=mask", timeout=2)
            if not mask:
                return

            logger.debug("[auth] Overlay mask detected; attempting to close.")
            iframe = self._page.get_frame("loginIfr", timeout=5)
            if not iframe:
                logger.debug("[auth] Login iframe not found.")
                return

            close_btn = iframe.ele("@id=close", timeout=5)
            if close_btn:
                close_btn.click()
                logger.debug("[auth] Closed overlay mask via iframe close button.")
            else:
                logger.debug("[auth] Close button not found in login iframe.")
        except Exception as e:
            logger.debug("[auth] Error handling overlay mask: %s", e)

    def _click_login_button(self, attempt: int) -> None:
        """
        Try to click the login button on the page.

        :param attempt: The current attempt number (for logging).
        """
        try:
            logger.debug("[auth] Attempting login click (#%s).", attempt)
            login_btn = self._page.ele("@id=login-btn", timeout=5)
            if login_btn:
                login_btn.click()
                logger.debug("[auth] Login button clicked.")
            else:
                logger.debug("[auth] Login button not found.")
        except Exception as e:
            logger.debug("[auth] Exception clicking login button: %s", e)

    def _manual_login(
        self,
        max_retries: int = 3,
    ) -> bool:
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
        if getattr(self, "_disable_images_orig", False):
            logger.debug("[auth] Temporarily enabling images for manual login.")
            self._options.no_imgs(False)
            self._restart_browser(headless=False)
        elif original_headless:
            self._restart_browser(headless=False)

        # 2. Navigate to home page
        try:
            self._page.get("https://www.qidian.com/")
        except Exception as e:
            logger.warning("[auth] Failed to load homepage for manual login: %s", e)
            return False

        # 3. Retry loop
        for attempt in range(1, max_retries + 1):
            if self._is_user_logged_in():
                logger.info("[auth] Detected successful login.")
                self._logged_in = True
                break

            logger.info(
                "[auth] Attempt %d/%d: Press Enter after completing login...",
                attempt,
                max_retries,
            )
            input()
        else:
            logger.warning("[auth] Manual login failed after %d attempts.", max_retries)
            self._logged_in = False
            return self._logged_in

        # 4. Restore headless if we changed it, then re-establish session
        if original_headless or getattr(self, "_disable_images_orig", False):
            logger.debug("[auth] Restoring browser settings after manual login...")
            self._options.no_imgs(self._disable_images_orig)
            self._restart_browser(headless=original_headless)
            self.login()
            if self._logged_in:
                logger.info(
                    "[auth] Login session successfully carried over after restart."
                )
            else:
                logger.warning(
                    "[auth] Lost login session after restoring headless mode."
                )

        return self._logged_in

    def _restart_browser(self, headless: Optional[bool] = None) -> None:
        """
        Shutdown the current browser and restart it with the given headless setting.

        :param headless: Whether to run the browser in headless mode.
        """
        if self._browser:
            self._browser.quit()
        self._clear_browser_refs()

        # Apply new headless setting and reinitialize
        if headless is not None:
            self._options.headless(headless)
            self._headless = headless
        self._setup()
        logger.debug("[browser] Browser restarted (headless=%s).", headless)

    def _build_book_info_url(self, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return f"{self.QIDIAN_BOOK_INFO_URL_2}/{book_id}/"

    def _build_chapter_url(self, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return f"{self.QIDIAN_CHAPTER_URL}/{book_id}/{chapter_id}/"

    def _build_bookcase_url(self) -> str:
        """
        Construct the URL for the user's bookcase page.

        :return: Fully qualified URL of the bookcase.
        """
        return self.QIDIAN_BOOKCASE_URL

    def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Retrieve the HTML of a Qidian book info page.

        This method enforces that the user is logged in, navigates to the
        book's info URL, waits a randomized delay to mimic human browsing,
        and returns the page HTML.

        :param book_id: The identifier of the book to fetch.
        :param wait_time: Base wait time in seconds before returning content.
                          If None, uses `self._config.wait_time`.
        :return: The HTML content of the book info page, or an empty string on error.
        """
        url = self._build_book_info_url(book_id)
        try:
            # Navigate and fetch
            self._page.get(url)

            # Randomized human‑like delay
            base = wait_time if wait_time is not None else self._config.wait_time
            sleep_with_random_delay(base, base * 0.2)

            html = str(self._page.html)
            logger.debug("[fetch] Fetched book info for ID %s from %s", book_id, url)
            return html

        except Exception as e:
            logger.warning("[fetch] Error fetching book info from '%s': %s", url, e)
            return ""

    def _scroll_page(self, presses: int, pause: float) -> None:
        """
        Scroll down by sending DOWN key presses to the page.

        :param presses: Number of DOWN key presses.
        :param pause: Seconds to wait between each press.
        """
        for _ in range(presses):
            try:
                self._page.actions.key_down(Keys.DOWN)
            except Exception as e:
                logger.debug("[page] Scroll press failed: %s", e)
            time.sleep(pause)

    def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Retrieve the HTML content of a specific chapter.

        Ensures the user is logged in, navigates to the chapter page,
        waits a randomized delay to mimic human reading, then scrolls
        to trigger any lazy‑loaded content.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :param wait_time: Base wait time in seconds before scrolling. If None,
                          falls back to `self._config.wait_time`.
        :return: The HTML content of the chapter page, or empty string on error.
        """
        url = self._build_chapter_url(book_id, chapter_id)
        try:
            # 1. Navigate to chapter URL
            self._page.get(url)

            # 2. Randomized human‑like delay
            base = wait_time if wait_time is not None else self._config.wait_time
            # sleep_with_random_delay(base, base*0.2)

            # 3. Scroll down to load dynamic content
            presses = int(random.uniform(base, base + 5) * 2)
            self._scroll_page(presses, pause=0.5)

            html = str(self._page.html)
            logger.debug("[fetch] Fetched chapter %s for book %s", chapter_id, book_id)
            return html

        except Exception as e:
            logger.warning("[fetch] Error fetching chapter from '%s': %s", url, e)
            return ""

    def get_bookcase(self, wait_time: Optional[int] = None) -> str:
        """
        Retrieve the HTML content of the logged‑in user's Qidian bookcase page.

        :param wait_time: Base number of seconds to wait before returning content.
                          If None, falls back to `self._config.wait_time`.
        :return: The HTML markup of the bookcase page, or empty string on error.
        :raises RuntimeError: If the user is not logged in.
        """
        if not self._logged_in:
            raise RuntimeError("User not logged in. Please call login() first.")

        url = self._build_bookcase_url()
        try:
            # Navigate to the bookcase page
            self._page.get(url)

            # Randomized human‑like delay
            base = wait_time if wait_time is not None else self._config.wait_time
            sleep_with_random_delay(base, base * 0.2)

            html = str(self._page.html)
            logger.debug("[fetch] Fetched bookcase HTML from %s", url)
            return html

        except Exception as e:
            logger.warning("[fetch] Error fetching bookcase from '%s': %s", url, e)
            return ""
