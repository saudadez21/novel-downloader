#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.yamibo.browser
---------------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseBrowser
from novel_downloader.models import FetcherConfig, LoginField


class YamiboBrowser(BaseBrowser):
    """
    A browser class for interacting with the Yamibo (www.yamibo.com) novel website.
    """

    BASE_URL = "https://www.yamibo.com"
    BOOKCASE_URL = "https://www.yamibo.com/my/fav"
    BOOK_INFO_URL = "https://www.yamibo.com/novel/{book_id}"
    CHAPTER_URL = "https://www.yamibo.com/novel/view-chapter?id={chapter_id}"

    LOGIN_URL = "https://www.yamibo.com/user/login"

    def __init__(
        self,
        config: FetcherConfig,
        reuse_page: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__("yamibo", config, reuse_page, **kwargs)

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        self._is_logged_in = await self._check_login_status()
        if self._is_logged_in:
            return True

        if not (username and password):
            self.logger.warning("[auth] No credentials provided.")
            return False

        for i in range(1, attempt + 1):
            login_page = await self.context.new_page()
            try:
                await login_page.goto(self.LOGIN_URL, wait_until="networkidle")

                await login_page.fill("#loginform-username", username)
                await login_page.fill("#loginform-password", password)

                before_url = login_page.url
                await login_page.click('button[name="login-button"]')

                try:
                    await login_page.wait_for_url(
                        lambda url, before_url=before_url: url_changed(url, before_url),
                        timeout=15000,
                    )
                except Exception as e:
                    self.logger.debug(
                        f"[auth] No URL change after login attempt {i}: {e}"
                    )

                self._is_logged_in = await self._check_login_status()
                if self._is_logged_in:
                    self.logger.info(f"[auth] Login successful on attempt {i}.")
                    return True
                else:
                    self.logger.warning(
                        f"[auth] Login check failed after attempt {i}. Retrying..."
                    )

            except Exception as e:
                self.logger.error(
                    f"[auth] Unexpected error during login attempt {i}: {e}"
                )
            finally:
                await login_page.close()

        self.logger.error(f"[auth] Login failed after {attempt} attempt(s).")
        return False

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
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]

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
                name="username",
                label="用户名",
                type="text",
                required=True,
                placeholder="请输入你的用户名",
                description="用于登录 www.yamibo.com 的用户名",
            ),
            LoginField(
                name="password",
                label="密码",
                type="password",
                required=True,
                placeholder="请输入你的密码",
                description="用于登录 www.yamibo.com 的密码",
            ),
        ]

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
        return "www.yamibo.com"

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "登录 - 百合会",
            "用户名/邮箱",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)


def url_changed(url: str, before: str) -> bool:
    return url != before
