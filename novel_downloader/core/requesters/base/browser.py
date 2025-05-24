#!/usr/bin/env python3
"""
novel_downloader.core.requesters.base.browser
---------------------------------------------

This module defines the BaseBrowser class, which provides common functionalities
for browser operations. Derived classes can extend these methods for
specialized purposes.
"""

import abc
import logging
import random
import time
import types
from typing import Any, Literal, Self, cast

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage._elements.chromium_element import ChromiumElement
from DrissionPage._pages.chromium_frame import ChromiumFrame
from DrissionPage._pages.mix_tab import MixTab
from DrissionPage.common import Keys

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.interfaces import SyncRequesterProtocol
from novel_downloader.utils.constants import (
    DEFAULT_USER_AGENT,
    DEFAULT_USER_DATA_DIR,
    DEFAULT_USER_PROFILE_NAME,
)


class BaseBrowser(SyncRequesterProtocol, abc.ABC):
    """
    BaseBrowser wraps basic browser operations using DrissionPage,
    with full control over browser configuration, session profile,
    retry and timeout behavior.

    Attributes:
        _options (ChromiumOptions): Configuration object for Chromium.
        _browser (Chromium): Chromium instance.
        _page (ChromiumPage): The active browser tab.
    """

    def is_async(self) -> Literal[False]:
        return False

    def __init__(
        self,
        config: RequesterConfig,
    ) -> None:
        """
        Initialize the Requester with a browser configuration.

        :param config: The RequesterConfig instance containing browser settings.
        """
        super().__init__()
        self._config = config
        self._options = ChromiumOptions()
        self._browser: Chromium | None = None
        self._page: MixTab | None = None
        self._headless: bool = config.headless

        user_data_path = (
            config.user_data_folder
            if self._is_valid(config.user_data_folder)
            else DEFAULT_USER_DATA_DIR
        )
        self._options.set_user_data_path(user_data_path)

        profile_name = (
            config.profile_name
            if self._is_valid(config.profile_name)
            else DEFAULT_USER_PROFILE_NAME
        )
        self._options.set_user(profile_name)

        self._options.headless(config.headless)
        self._options.set_user_agent(DEFAULT_USER_AGENT)
        self._options.set_timeouts(base=config.timeout)
        self._options.set_retry(
            times=config.retry_times, interval=config.backoff_factor
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

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self._init_browser()

    def _init_browser(self) -> None:
        """
        Set up the browser instance and open the default tab.
        """
        if not self._browser:
            self._browser = Chromium(self._options)
        if not self._page:
            self._page = cast(MixTab, self._browser.get_tab())

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
        :param wait_time: Base number of seconds to wait before returning content.
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
        :param wait_time: Base number of seconds to wait before returning content.
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

        Subclasses that support login+bookcase retrieval should override this.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML markup of the bookcase page.
        :raises NotImplementedError: If bookcase fetching is not supported.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this browser type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    def scroll_page(
        self,
        presses: int,
        pause: float = 0.5,
        jitter: float = 0.1,
    ) -> None:
        """
        Scroll down by sending DOWN key presses to the page.

        :param presses: Number of DOWN key presses.
        :param pause: Seconds to wait between each press.
        """
        for _ in range(int(presses)):
            try:
                self.page.actions.key_down(Keys.DOWN)
            except Exception as e:
                self.logger.debug("[page] Scroll press failed: %s", e)
            actual_pause = pause + random.uniform(-jitter, jitter)
            actual_pause = max(0, actual_pause)
            time.sleep(actual_pause)

    def click_button(
        self,
        locator: str | tuple[str, str] | ChromiumElement,
        timeout: float = 5.0,
        page: MixTab | ChromiumFrame | None = None,
    ) -> bool:
        """
        Attempt to locate and click a button on the page.

        :param locator: The target element to click.
        :param timeout: Maximum time (in seconds) to wait.
        :param page: Optional page or frame to search in.
        :return: True if the element was located and clicked; False otherwise.
        """
        try:
            page = page or self.page
            btn = page.ele(locator, timeout=timeout)
            if isinstance(btn, ChromiumElement):
                btn.click()
                return True
        except Exception as e:
            self.logger.debug("[browser] Exception clicking button: %s", e)
        return False

    def get_frame(
        self,
        loc_ind_ele: str | int | ChromiumFrame | ChromiumElement,
        timeout: float = 5.0,
        page: MixTab | ChromiumFrame | None = None,
    ) -> ChromiumFrame | None:
        """
        Attempt to locate and return a frame from the page.

        :param loc_ind_ele: The frame to locate.
        :param timeout: Maximum time (in seconds) to wait.
        :param page: Optional page or frame to search in.
        :return: The located ChromiumFrame if found; otherwise, None.
        """
        try:
            page = page or self.page
            return page.get_frame(loc_ind_ele, timeout=timeout)
        except Exception as e:
            self.logger.debug(
                "[browser] Exception occurred while getting frame [%s]: %s",
                loc_ind_ele,
                e,
            )
        return None

    def restart_browser(
        self,
        headless: bool | None = None,
    ) -> None:
        """
        Shutdown the current browser and restart it with the given headless setting.

        :param headless: Whether to run the browser in headless mode.
        """
        if self._browser:
            self._browser.quit()
        self._browser = None
        self._page = None

        # Apply new headless setting and reinitialize
        if headless is not None:
            self._options.headless(headless)
            self._headless = headless
        self._init_browser()
        self.logger.debug("[browser] Browser restarted (headless=%s).", headless)

    @property
    def page(self) -> MixTab:
        """
        Return the current Chromium page object.

        :return: ChromiumPage instance of the current tab.
        """
        if self._page is None:
            raise RuntimeError("Page is not initialized or has been shut down.")
        return self._page

    @property
    def browser(self) -> Chromium:
        """
        Return the Chromium browser instance.

        :return: Chromium instance used by this browser.
        """
        if self._browser is None:
            raise RuntimeError("Browser is not initialized or has been shut down.")
        return self._browser

    @staticmethod
    def _is_valid(value: str) -> bool:
        return bool(value and value.strip())

    def close(self) -> None:
        """
        Shutdown the browser session and release resources.

        This quits the Chromium instance and clears references to browser and page.
        """
        if self._browser and self._config.auto_close:
            self._browser.quit()
        self._browser = None
        self._page = None

    def __enter__(self) -> Self:
        self._init_browser()
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
        Prepare object state for serialization (e.g., pickling).

        Removes browser-related fields that cannot be pickled.

        :return: A dict representing the serializable object state.
        """
        state = self.__dict__.copy()
        state.pop("_browser", None)
        state.pop("_page", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Restore object state after deserialization.

        Automatically reinitializes the browser setup.

        :param state: The saved state dictionary.
        """
        self.__dict__.update(state)
        self._init_browser()
