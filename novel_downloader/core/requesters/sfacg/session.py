"""
novel_downloader.core.requesters.sfacg.session
----------------------------------------------

"""

from http.cookies import SimpleCookie
from typing import Any

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base import BaseSession
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr


class SfacgSession(BaseSession):
    """
    A session class for interacting with the
    Sfacg (m.sfacg.com) novel website.
    """

    BOOKCASE_URL = "https://m.sfacg.com/sheets/"
    BOOK_INFO_URL = "https://m.sfacg.com/b/{book_id}/"
    BOOK_CATALOG_URL = "https://m.sfacg.com/i/{book_id}/"
    CHAPTER_URL = "https://m.sfacg.com/c/{chapter_id}/"

    def __init__(
        self,
        config: RequesterConfig,
    ):
        super().__init__(config)
        self._logged_in: bool = False
        self._retry_times = config.retry_times

    def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Restore cookies persisted by the session-based workflow.
        """
        cookies: dict[str, str] = state_mgr.get_cookies("sfacg")

        self.update_cookies(cookies)
        for attempt in range(1, self._retry_times + 1):
            if self._check_login_status():
                self.logger.debug("[auth] Already logged in.")
                self._logged_in = True
                return True

            if attempt == 1:
                print(t("session_login_prompt_intro"))
            cookie_str = input(
                t(
                    "session_login_prompt_paste_cookie",
                    attempt=attempt,
                    max_retries=self._retry_times,
                )
            ).strip()

            cookies = self._parse_cookie_input(cookie_str)
            if not cookies:
                print(t("session_login_prompt_invalid_cookie"))
                continue

            self.update_cookies(cookies)
        self._logged_in = self._check_login_status()
        return self._logged_in

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info and catalog pages.

        Order: [info, catalog]

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        info_url = self.book_info_url(book_id=book_id)
        catalog_url = self.book_catalog_url(book_id=book_id)

        pages = []
        try:
            resp = self.get(info_url, **kwargs)
            resp.raise_for_status()
            pages.append(resp.text)
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(info:%s) failed: %s",
                book_id,
                exc,
            )
            pages.append("")

        try:
            resp = self.get(catalog_url, **kwargs)
            resp.raise_for_status()
            pages.append(resp.text)
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(catalog:%s) failed: %s",
                book_id,
                exc,
            )
            pages.append("")

        return pages

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the HTML of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_chapter(%s) failed: %s",
                book_id,
                exc,
            )
        return []

    def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        url = self.bookcase_url()
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_bookcase failed: %s",
                exc,
            )
        return []

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
    def book_catalog_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's catalog page.

        :param book_id: The identifier of the book.
        :return: Fully qualified catalog page URL.
        """
        return cls.BOOK_CATALOG_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(chapter_id=chapter_id)

    def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "请输入用户名和密码",
            "用户未登录",
            "可输入用户名",
        ]
        resp_text = self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    @staticmethod
    def _parse_cookie_input(cookie_str: str) -> dict[str, str]:
        """
        Parse a raw cookie string (e.g. from browser dev tools) into a dict.
        Returns an empty dict if parsing fails.

        :param cookie_str: The raw cookie header string.
        :return: Parsed cookie dict.
        """
        filtered = "; ".join(pair for pair in cookie_str.split(";") if "=" in pair)
        parsed = SimpleCookie()
        try:
            parsed.load(filtered)
            return {k: v.value for k, v in parsed.items()}
        except Exception:
            return {}

    def _on_close(self) -> None:
        """
        Save cookies to the state manager before closing.
        """
        state_mgr.set_cookies("sfacg", self.cookies)
