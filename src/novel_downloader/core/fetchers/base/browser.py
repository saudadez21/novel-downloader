#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.base.browser
-------------------------------------------

"""

import abc
import logging
import types
from typing import Any, Literal, Self

from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    ViewportSize,
    async_playwright,
)

from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import FetcherConfig, LoginField, NewContextOptions
from novel_downloader.utils.constants import (
    DATA_DIR,
    DEFAULT_USER_AGENT,
)

from .rate_limiter import TokenBucketRateLimiter

_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
window.chrome = { runtime: {} };
""".strip()


class BaseBrowser(FetcherProtocol, abc.ABC):
    """
    BaseBrowser wraps basic browser operations using playwright
    """

    def __init__(
        self,
        site: str,
        config: FetcherConfig,
        reuse_page: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async browser with configuration.

        :param config: Configuration object for session behavior
        """
        self._site = site
        self._config = config

        self._state_file = DATA_DIR / site / "browser_state.cookies"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        self._is_logged_in = False
        self._reuse_page = reuse_page
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._manual_page: Page | None = None
        self._rate_limiter: TokenBucketRateLimiter | None = None

        if config.max_rps is not None and config.max_rps > 0:
            self._rate_limiter = TokenBucketRateLimiter(config.max_rps)

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
        """
        return False

    @abc.abstractmethod
    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        ...

    @abc.abstractmethod
    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        ...

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.
        Subclasses that support user login/bookcase should override this.

        :return: The HTML of the bookcase page.
        """
        raise NotImplementedError(
            "Bookcase fetching is not supported by this session type. "
            "Override get_bookcase() in your subclass to enable it."
        )

    async def init(
        self,
        headless: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Set up the playwright.
        """
        if self._pw is None:
            self._pw = await async_playwright().start()

        if self._browser is None or not self._browser.is_connected():
            browser_cls: BrowserType = getattr(self._pw, self.browser_type)

            launch_args: dict[str, Any] = {
                "headless": headless and self.headless,
            }
            if self._config.proxy:
                launch_args["proxy"] = {"server": self._config.proxy}

            self._browser = await browser_cls.launch(**launch_args)

        if self._context is None:
            context_args: NewContextOptions = {
                "user_agent": self.user_agent,
                "locale": "zh-CN",
                "viewport": ViewportSize(width=1280, height=800),
                "java_script_enabled": True,
                "ignore_https_errors": not self._config.verify_ssl,
            }

            if self._config.headers:
                context_args["extra_http_headers"] = self._config.headers

            self._context = await self._browser.new_context(**context_args)
            await self._context.add_init_script(_STEALTH_SCRIPT)
            self._context.set_default_timeout(self.timeout * 1000)

    async def close(self) -> None:
        """
        Shutdown and clean up the broswer.
        """
        if self._page:
            await self._page.close()
        self._page = None
        if self._manual_page:
            await self._manual_page.close()
        self._manual_page = None
        if self._context:
            await self._context.close()
        self._context = None
        if self._browser:
            await self._browser.close()
        self._browser = None
        if self._pw:
            await self._pw.stop()
        self._pw = None

    async def fetch(
        self,
        url: str,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"]
        | None = "load",
        referer: str | None = None,
        **kwargs: Any,
    ) -> str:
        if self._reuse_page:
            return await self._fetch_with_reuse(url, wait_until, referer, **kwargs)
        else:
            return await self._fetch_with_new(url, wait_until, referer, **kwargs)

    async def load_state(self) -> bool:
        """ """
        if not self._state_file.exists() or self._context is None:
            return False
        try:
            if self._context is not None:
                await self._context.close()
            context_args: NewContextOptions = {
                "user_agent": self.user_agent,
                "locale": "zh-CN",
                "viewport": ViewportSize(width=1280, height=800),
                "java_script_enabled": True,
                "ignore_https_errors": not self._config.verify_ssl,
                "storage_state": self._state_file,
            }

            if self._config.headers:
                context_args["extra_http_headers"] = self._config.headers

            self._context = await self.browser.new_context(**context_args)
            self._context.set_default_timeout(self.timeout * 1000)
            await self._context.add_init_script(_STEALTH_SCRIPT)
            self._is_logged_in = await self._check_login_status()
            return self._is_logged_in
        except Exception as e:
            self.logger.warning("Failed to load state: %s", e)
        return False

    async def save_state(self) -> bool:
        """ """
        if self._context is None:
            return False
        try:
            await self._context.storage_state(path=self._state_file)
            return True
        except Exception as e:
            self.logger.warning("Failed to save state: %s", e)
        return False

    async def set_interactive_mode(self, enable: bool) -> bool:
        """
        Enable or disable interactive mode for manual login.

        :param enable: True to enable, False to disable interactive mode.
        :return: True if operation or login check succeeded, False otherwise.
        """
        return False

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        return False

    async def _restart_browser(
        self,
        headless: bool = True,
    ) -> None:
        """
        Shutdown the current browser and restart it with the given headless setting.

        :param headless: Whether to run the browser in headless mode.
        """
        await self.close()

        # Apply new headless setting and reinitialize
        await self.init(headless=headless)
        self.logger.debug("[browser] Browser restarted (headless=%s).", headless)

    async def _fetch_with_new(
        self,
        url: str,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"]
        | None = "load",
        referer: str | None = None,
        **kwargs: Any,
    ) -> str:
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until=wait_until, referer=referer, **kwargs)
            html: str = await page.content()
            return html
        finally:
            await page.close()

    async def _fetch_with_reuse(
        self,
        url: str,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"]
        | None = "load",
        referer: str | None = None,
        **kwargs: Any,
    ) -> str:
        if not self._page:
            self._page = await self.context.new_page()
        await self._page.goto(url, wait_until=wait_until, referer=referer, **kwargs)
        html: str = await self._page.content()
        return html

    @property
    def hostname(self) -> str:
        return ""

    @property
    def site(self) -> str:
        return self._site

    @property
    def requester_type(self) -> str:
        return "browser"

    @property
    def is_logged_in(self) -> bool:
        """
        Indicates whether the requester is currently authenticated.
        """
        return self._is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return []

    @property
    def browser(self) -> Browser:
        """
        Return the active playwright.Browser.

        :raises RuntimeError: If the browser is uninitialized.
        """
        if self._browser is None:
            raise RuntimeError("Browser is not initialized or has been shut down.")
        return self._browser

    @property
    def context(self) -> BrowserContext:
        """
        Return the active playwright.BrowserContext.

        :raises RuntimeError: If the context is uninitialized.
        """
        if self._context is None:
            raise RuntimeError(
                "BrowserContext is not initialized or has been shut down."
            )
        return self._context

    @property
    def headless(self) -> bool:
        return self._config.headless

    @property
    def user_agent(self) -> str:
        ua = self._config.user_agent or ""
        return ua.strip() or DEFAULT_USER_AGENT

    @property
    def browser_type(self) -> str:
        return self._config.browser_type

    @property
    def disable_images(self) -> bool:
        return self._config.disable_images

    @property
    def retry_times(self) -> int:
        return self._config.retry_times

    @property
    def request_interval(self) -> float:
        return self._config.request_interval

    @property
    def backoff_factor(self) -> float:
        return self._config.backoff_factor

    @property
    def timeout(self) -> float:
        return self._config.timeout

    @property
    def max_connections(self) -> int:
        return self._config.max_connections

    async def __aenter__(self) -> Self:
        await self.init()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        await self.close()
