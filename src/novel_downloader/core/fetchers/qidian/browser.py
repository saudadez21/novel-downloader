#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.qidian.browser
---------------------------------------------

"""

import asyncio
from typing import Any

from playwright.async_api import Page

from novel_downloader.core.fetchers.base import BaseBrowser
from novel_downloader.models import FetcherConfig, LoginField
from novel_downloader.utils.i18n import t


class QidianBrowser(BaseBrowser):
    """
    A browser class for interacting with the Qidian (www.qidian.com) novel website.
    """

    HOMEPAGE_URL = "https://www.qidian.com/"
    BOOKCASE_URL = "https://my.qidian.com/bookcase/"
    # BOOK_INFO_URL = "https://book.qidian.com/info/{book_id}/"
    BOOK_INFO_URL = "https://www.qidian.com/book/{book_id}/"
    CHAPTER_URL = "https://www.qidian.com/chapter/{book_id}/{chapter_id}/"

    LOGIN_URL = "https://passport.qidian.com/"

    def __init__(
        self,
        config: FetcherConfig,
        reuse_page: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__("qidian", config, reuse_page, **kwargs)

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        self._is_logged_in = await self._check_login_status()
        return self._is_logged_in

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        catalog_url = self.book_info_url(book_id=book_id)
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, referer=catalog_url, **kwargs)]

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        url = self.bookcase_url()
        return [await self.fetch(url, **kwargs)]

    async def get_homepage(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the site home page.

        :return: The HTML markup of the home page.
        """
        url = self.homepage_url()
        return [await self.fetch(url, **kwargs)]

    async def set_interactive_mode(self, enable: bool) -> bool:
        """
        Enable or disable interactive mode for manual login.

        :param enable: True to enable, False to disable interactive mode.
        :return: True if operation or login check succeeded, False otherwise.
        """
        if enable:
            if self.headless:
                await self._restart_browser(headless=False)
            if self._manual_page is None:
                self._manual_page = await self.context.new_page()
            await self._manual_page.goto(self.LOGIN_URL)
            return True

        # restore
        if self._manual_page:
            await self._manual_page.close()
        self._manual_page = None
        if self.headless:
            await self._restart_browser(headless=True)
            self._is_logged_in = await self._check_login_status()
        return self.is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="manual_login",
                label="手动登录",
                type="manual_login",
                required=True,
                description=t("login_prompt_intro"),
            )
        ]

    @classmethod
    def homepage_url(cls) -> str:
        """
        Construct the URL for the site home page.

        :return: Fully qualified URL of the home page.
        """
        return cls.HOMEPAGE_URL

    @classmethod
    def bookcase_url(cls) -> str:
        """
        Construct the URL for the user's bookcase page.

        :return: Fully qualified URL of the bookcase.
        """
        return cls.BOOKCASE_URL

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

    @property
    def hostname(self) -> str:
        return "www.qidian.com"

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by inspecting
        the visibility of the 'sign-in' element on the homepage.

        :return: True if the user appears to be logged in, False otherwise.
        """
        try:
            page = await self.context.new_page()
            await self._login_auto(page)
            await self._dismiss_overlay(page)
            await page.goto(self.HOMEPAGE_URL, wait_until="networkidle")
            sign_in_elem = await page.query_selector("#login-box .sign-in")
            sign_out_elem = await page.query_selector("#login-box .sign-out")

            sign_in_class = (
                (await sign_in_elem.get_attribute("class") or "")
                if sign_in_elem
                else ""
            )
            sign_out_class = (
                (await sign_out_elem.get_attribute("class") or "")
                if sign_out_elem
                else ""
            )

            sign_in_hidden = "hidden" in sign_in_class
            sign_out_hidden = "hidden" in sign_out_class

            await page.close()

            # if sign_in_visible and not sign_out_visible:
            if not sign_in_hidden and sign_out_hidden:
                self.logger.debug("[auth] Detected as logged in.")
                return True
            else:
                self.logger.debug("[auth] Detected as not logged in.")
                return False
        except Exception as e:
            self.logger.warning("[auth] Error while checking login status: %s", e)
        return False

    async def _dismiss_overlay(
        self,
        page: Page,
        timeout: float = 2.0,
    ) -> None:
        """
        Detect and close any full-page overlay mask that might block the login UI.
        """
        try:
            mask = await page.wait_for_selector("div.mask", timeout=timeout * 1000)
            if not mask or not await mask.is_visible():
                return

            self.logger.debug("[auth] Overlay mask detected; attempting to close.")

            iframe_element = await page.wait_for_selector(
                "#loginIfr",
                timeout=timeout * 1000,
            )
            if iframe_element is None:
                self.logger.debug("[auth] Login iframe not found.")
                return

            iframe = await iframe_element.content_frame()
            if iframe is None:
                self.logger.debug("[auth] Unable to access iframe content.")
                return

            # 点击关闭按钮
            await iframe.click("#close", timeout=2000)
            self.logger.debug("[auth] Overlay mask closed.")

        except Exception as e:
            self.logger.debug("[auth] Error handling overlay mask: %s", e)

    async def _login_auto(
        self,
        page: Page,
        timeout: float = 5.0,
    ) -> None:
        """
        Attempt one automatic login interaction (click once and check).

        :param page: Playwright Page object to interact with.
        :param timeout: Seconds to wait for login box to appear.
        :return: True if login successful or already logged in; False otherwise.
        """
        try:
            await page.goto("https://www.qidian.com/", wait_until="networkidle")
            await page.wait_for_selector("#login-box", timeout=timeout * 1000)
        except Exception as e:
            self.logger.warning("[auth] Failed to load login box: %s", e)
            return

        self.logger.debug("[auth] Clicking login button once.")
        try:
            btn = await page.query_selector("#login-btn")
            if btn and await btn.is_visible():
                await btn.click()
                tasks = [
                    asyncio.create_task(
                        page.wait_for_selector(
                            "div.mask",
                            timeout=timeout * 1000,
                        )
                    ),
                    asyncio.create_task(
                        page.wait_for_selector(
                            "div.qdlogin-wrap",
                            timeout=timeout * 1000,
                        )
                    ),
                    asyncio.create_task(
                        page.wait_for_url(
                            lambda url: "login" not in url,
                            timeout=timeout * 1000,
                        )
                    ),
                ]
                done, pending = await asyncio.wait(
                    tasks,
                    timeout=timeout + 1,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                if done:
                    self.logger.debug("[auth] Login flow proceeded after button click.")
                else:
                    self.logger.warning("[auth] Timeout waiting for login to proceed.")
        except Exception as e:
            self.logger.debug("[auth] Failed to click login button: %s", e)
        return
