#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.base_browser
---------------------------------------------

This module defines the BaseBrowser class, which provides common functionalities
for browser operations. Derived classes can extend these methods for
specialized purposes.
"""

import abc
import logging
from typing import Any, Dict, Optional

from DrissionPage import Chromium, ChromiumOptions, ChromiumPage

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.interfaces import RequesterProtocol
from novel_downloader.utils.constants import (
    DEFAULT_USER_AGENT,
    DEFAULT_USER_DATA_DIR,
    DEFAULT_USER_PROFILE_NAME,
)

logger = logging.getLogger(__name__)


def _is_valid(value: str) -> bool:
    return bool(value and value.strip())


class BaseBrowser(RequesterProtocol, abc.ABC):
    """
    BaseBrowser wraps basic browser operations using DrissionPage,
    with full control over browser configuration, session profile,
    retry and timeout behavior.

    Attributes:
        _options (ChromiumOptions): Configuration object for Chromium.
        _browser (Chromium): Chromium instance.
        _page (ChromiumPage): The active browser tab.
    """

    def _init_browser(self, config: RequesterConfig) -> None:
        """
        Initialize the browser with specified options from RequesterConfig.

        :param config: Configuration settings for
                        browser behavior, profile, timeouts, etc.
        """
        self._config = config
        self._options = ChromiumOptions()

        user_data_path = (
            config.user_data_folder
            if _is_valid(config.user_data_folder)
            else DEFAULT_USER_DATA_DIR
        )
        if _is_valid(config.user_data_folder):
            logger.warning(
                "[browser] Using user_data_folder='%s'. "
                "This may interfere with an active Chrome session. "
                "Do NOT use this profile in both the browser and "
                "this script at the same time.",
                config.user_data_folder,
            )
        self._options.set_user_data_path(user_data_path)

        profile_name = (
            config.profile_name
            if _is_valid(config.profile_name)
            else DEFAULT_USER_PROFILE_NAME
        )
        self._options.set_user(profile_name)

        self._options.headless(config.headless)
        self._options.set_user_agent(DEFAULT_USER_AGENT)
        self._options.set_timeouts(base=config.wait_time)
        self._options.set_retry(
            times=config.retry_times, interval=config.retry_interval
        )

        self._disable_images_orig = config.disable_images
        if config.disable_images:
            self._options.no_imgs(True)
        if config.mute_audio:
            self._options.mute(True)

        # self._options.set_argument('--disable-blink-features', 'AutomationControlled')
        # self._options.set_argument('--log-level', '3')
        # self._options.set_argument('--disable-gpu')
        # self._options.set_argument('no-sandbox')

        self._setup()

    def _setup(self) -> None:
        """
        Set up the browser instance and open the default tab.
        """
        self._browser = Chromium(self._options)
        self._page = self._browser.get_tab()

    def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Attempt to log in
        """
        raise NotImplementedError(
            "Login is not supported by this browser type. "
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

        Subclasses that support login+bookcase retrieval should override this.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML markup of the bookcase page.
        :raises NotImplementedError: If bookcase fetching is not supported.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this browser type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    @property
    def page(self) -> ChromiumPage:
        """
        Return the current Chromium page object.

        :return: ChromiumPage instance of the current tab.
        """
        return self._page

    @property
    def browser(self) -> Chromium:
        """
        Return the Chromium browser instance.

        :return: Chromium instance used by this browser.
        """
        return self._browser

    def _clear_browser_refs(self) -> None:
        """
        Clear internal browser/page references without quitting.
        """
        self._browser = None
        self._page = None

    def shutdown(self) -> None:
        """
        Shutdown the browser session and release resources.

        This quits the Chromium instance and clears references to browser and page.
        """
        if self._browser:
            self._browser.quit()
        self._clear_browser_refs()

    def __getstate__(self) -> Dict[str, Any]:
        """
        Prepare object state for serialization (e.g., pickling).

        Removes browser-related fields that cannot be pickled.

        :return: A dict representing the serializable object state.
        """
        state = self.__dict__.copy()
        state.pop("_browser", None)
        state.pop("_page", None)
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """
        Restore object state after deserialization.

        Automatically reinitializes the browser setup.

        :param state: The saved state dictionary.
        """
        self.__dict__.update(state)
        self._setup()
