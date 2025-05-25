"""
novel_downloader.core.requesters.yamibo.session
-----------------------------------------------

"""

from typing import Any

from lxml import etree

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base import BaseSession
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import sleep_with_random_delay


class YamiboSession(BaseSession):
    """
    A session class for interacting with the
    yamibo (www.yamibo.com) novel website.
    """

    BASE_URL = "https://www.yamibo.com"
    BOOKCASE_URL = "https://www.yamibo.com/my/fav"
    BOOK_INFO_URL = "https://www.yamibo.com/novel/{book_id}"
    CHAPTER_URL = "https://www.yamibo.com/novel/view-chapter?id={chapter_id}"

    LOGIN_URL = "https://www.yamibo.com/user/login"

    def __init__(
        self,
        config: RequesterConfig,
    ):
        super().__init__(config)
        self._logged_in: bool = False
        self._request_interval = config.backoff_factor
        self._retry_times = config.retry_times
        self._username = config.username
        self._password = config.password

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
        cookies: dict[str, str] = state_mgr.get_cookies("yamibo")
        username = username or self._username
        password = password or self._password

        self.update_cookies(cookies)
        for _ in range(self._retry_times):
            if self._check_login_status():
                self.logger.debug("[auth] Already logged in.")
                self._logged_in = True
                return True
            if username and password and not self._api_login(username, password):
                print(t("session_login_failed", site="esjzone"))
            sleep_with_random_delay(
                self._request_interval,
                mul_spread=1.1,
                max_sleep=self._request_interval + 2,
            )

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
        url = self.book_info_url(book_id=book_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(%s) failed: %s",
                book_id,
                exc,
            )
        return []

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
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(chapter_id=chapter_id)

    def _api_login(self, username: str, password: str) -> bool:
        """
        Login to the API using a 2-step token-based process.

        Step 1: Get token `_csrf-frontend`.
        Step 2: Use token and credentials to perform login.
        Return True if login succeeds, False otherwise.
        """
        try:
            resp_1 = self.get(self.LOGIN_URL)
            resp_1.raise_for_status()
            tree = etree.HTML(resp_1.text)
            csrf_value = tree.xpath('//input[@name="_csrf-frontend"]/@value')
            csrf_value = csrf_value[0] if csrf_value else ""
            if not csrf_value:
                self.logger.warning("[session] _api_login: CSRF token not found.")
                return False
        except Exception as exc:
            self.logger.warning("[session] _api_login failed at step 1: %s", exc)
            return False

        data_2 = {
            "_csrf-frontend": csrf_value,
            "LoginForm[username]": username,
            "LoginForm[password]": password,
            # "LoginForm[rememberMe]": 0,
            "LoginForm[rememberMe]": 1,
            "login-button": "",
        }
        temp_headers = dict(self.headers)
        temp_headers["Origin"] = self.BASE_URL
        temp_headers["Referer"] = self.LOGIN_URL
        try:
            resp_2 = self.post(self.LOGIN_URL, data=data_2, headers=temp_headers)
            resp_2.raise_for_status()
            return "登录成功" in resp_2.text
        except Exception as exc:
            self.logger.warning("[session] _api_login failed at step 2: %s", exc)
        return False

    def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "登录 - 百合会",
            "用户名/邮箱",
        ]
        resp_text = self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    def _on_close(self) -> None:
        """
        Save cookies to the state manager before closing.
        """
        state_mgr.set_cookies("yamibo", self.cookies)
