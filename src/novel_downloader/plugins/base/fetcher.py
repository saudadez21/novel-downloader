#!/usr/bin/env python3
"""
novel_downloader.plugins.base.fetcher
-------------------------------------

Abstract base class providing common HTTP session handling for fetchers.
"""

import abc
import asyncio
import json
import logging
import types
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Literal, Self
from urllib.parse import unquote, urlparse

import aiohttp
from aiohttp import ClientResponse, ClientSession, ClientTimeout, TCPConnector

from novel_downloader.infra.http_defaults import (
    DEFAULT_IMAGE_SUFFIX,
    DEFAULT_USER_HEADERS,
)
from novel_downloader.infra.paths import DATA_DIR
from novel_downloader.libs.filesystem import sanitize_filename
from novel_downloader.libs.filesystem.file import _unique_path, write_file
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.utils.rate_limiter import TokenBucketRateLimiter
from novel_downloader.schemas import FetcherConfig, LoginField


class BaseSession(abc.ABC):
    """
    BaseSession wraps basic HTTP operations using aiohttp.ClientSession.
    """

    site_name: str
    BASE_URL_MAP: dict[str, str] = {}
    DEFAULT_BASE_URL: str = ""

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the async session with configuration.

        :param config: Configuration object for session behavior
        :param cookies: Optional initial cookies to set on the session.
        """
        self._base_url = self._resolve_base_url(config.locale_style)
        self._backoff_factor = config.backoff_factor
        self._request_interval = config.request_interval
        self._retry_times = config.retry_times
        self._timeout = config.timeout
        self._max_connections = config.max_connections
        self._verify_ssl = config.verify_ssl
        self._init_cookies = cookies or {}
        self._is_logged_in = False

        self._state_file = DATA_DIR / self.site_name / "session_state.cookies"

        self._headers = (
            config.headers.copy()
            if config.headers is not None
            else DEFAULT_USER_HEADERS.copy()
        )
        if config.user_agent:
            self._headers["User-Agent"] = config.user_agent

        self._session: ClientSession | None = None
        self._rate_limiter: TokenBucketRateLimiter | None = (
            TokenBucketRateLimiter(config.max_rps) if config.max_rps > 0 else None
        )

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Set up the aiohttp.ClientSession with timeout, connector, headers.
        """
        timeout = ClientTimeout(total=self._timeout)
        connector = TCPConnector(
            ssl=self._verify_ssl,
            limit_per_host=self._max_connections,
        )
        self._session = ClientSession(
            timeout=timeout,
            connector=connector,
            cookies=self._init_cookies,
        )

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None

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
        :return: The page content as string list.
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
        :return: The page content as string list.
        """
        ...

    async def download_images(
        self,
        img_dir: Path,
        urls: list[str],
        batch_size: int = 10,
        *,
        on_exist: Literal["overwrite", "skip", "rename"] = "skip",
    ) -> None:
        """
        Download images to `img_dir` in batches.

        Any HTTP error (raise_for_status) is logged and skipped.

        :param img_dir: Destination folder.
        :param urls: List of image URLs (http/https).
        :param batch_size: Concurrency per batch.
        :param on_exist: What to do when file exists.
        """
        if not urls:
            return

        img_dir.mkdir(parents=True, exist_ok=True)

        for i in range(0, len(urls), max(1, batch_size)):
            batch = urls[i : i + batch_size]
            tasks = [
                self._download_one_image(url, img_dir, on_exist=on_exist)
                for url in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    self.logger.warning("Image download error: %s", r)

    @property
    def is_logged_in(self) -> bool:
        """
        Indicates whether the requester is currently authenticated.
        """
        return self._is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return []

    async def fetch(
        self,
        url: str,
        encoding: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Fetch the content from the given URL asynchronously, with retry support.

        :param url: The target URL to fetch.
        :param kwargs: Additional keyword arguments to pass to `session.get`.
        :return: The response body as text.
        :raises: aiohttp.ClientError on final failure.
        """
        if self._rate_limiter:
            await self._rate_limiter.wait()

        for attempt in range(self._retry_times + 1):
            try:
                async with await self.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    return await self._response_to_str(resp, encoding)
            except aiohttp.ClientError:
                if attempt < self._retry_times:
                    await async_jitter_sleep(
                        self._backoff_factor,
                        mul_spread=1.1,
                        max_sleep=self._backoff_factor + 2,
                    )
                    continue
                raise

        raise RuntimeError("Unreachable code reached in fetch()")

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """
        Send an HTTP GET request asynchronously.

        :param url: The target URL.
        :param params: Query parameters to include in the request.
        :param kwargs: Additional args passed to session.get().
        :return: aiohttp.ClientResponse object.
        :raises RuntimeError: If the session is not initialized.
        """
        return await self._request("GET", url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: dict[str, Any] | bytes | None = None,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ClientResponse:
        """
        Send an HTTP POST request asynchronously.

        :param url: The target URL.
        :param data: Form data to include in the request body.
        :param json: JSON body to include in the request.
        :param kwargs: Additional args passed to session.post().
        :return: aiohttp.ClientResponse object.
        :raises RuntimeError: If the session is not initialized.
        """
        return await self._request("POST", url, data=data, json=json, **kwargs)

    async def load_state(self) -> bool:
        """
        Load session cookies from a file to restore previous login state.

        :return: True if the session state was loaded, False otherwise.
        """
        # if not self._state_file.exists() or self._session is None:
        #     return False
        # try:
        #     self._session.cookie_jar.load(self._state_file)
        #     self._is_logged_in = await self._check_login_status()
        #     return self._is_logged_in
        # except Exception as e:
        #     self.logger.warning("Failed to load state: %s", e)
        # return False
        if not self._state_file.exists() or self._session is None:
            return False
        try:
            storage = json.loads(self._state_file.read_text(encoding="utf-8"))
            raw_cookies = storage.get("cookies", [])
            cookie_dict = self._filter_cookies(raw_cookies)

            if cookie_dict:
                self._session.cookie_jar.update_cookies(cookie_dict)

            self._is_logged_in = await self._check_login_status()
            return self._is_logged_in
        except Exception as e:
            self.logger.warning("Failed to load state: %s", e)
            return False

    async def save_state(self) -> bool:
        """
        Save the current session cookies to a file for future reuse.

        :return: True if the session state was saved, False otherwise.
        """
        # if self._session is None:
        #     return False
        # try:
        #     self._session.cookie_jar.save(self._state_file)
        #     return True
        # except Exception as e:
        #     self.logger.warning("Failed to save state: %s", e)
        # return False
        if self._session is None:
            return False
        try:
            cookies = []
            for cookie in self._session.cookie_jar:
                cookies.append(
                    {
                        "name": cookie.key,
                        "value": cookie.value,
                    }
                )
            storage_state = {
                "cookies": cookies,
                "origins": [],
            }
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(storage_state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return True
        except Exception as e:
            self.logger.warning("Failed to save state: %s", e)
            return False

    def update_cookies(
        self,
        cookies: dict[str, str],
    ) -> None:
        """
        Update or add multiple cookies in the session.

        :param cookies: A dictionary of cookie key-value pairs.
        """
        if self._session:
            self._session.cookie_jar.update_cookies(cookies)

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> ClientResponse:
        headers = {**self._headers, **kwargs.pop("headers", {})}
        return await self.session.request(method, url, headers=headers, **kwargs)

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        return False

    @property
    def session(self) -> ClientSession:
        """
        Return the active aiohttp.ClientSession.

        :raises RuntimeError: If the session is uninitialized.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")
        return self._session

    async def _sleep(self) -> None:
        if self._request_interval > 0:
            await async_jitter_sleep(
                self._request_interval,
                mul_spread=1.1,
                max_sleep=self._request_interval + 2,
            )

    @property
    def headers(self) -> dict[str, str]:
        """
        Get a copy of the current session headers for temporary use.

        :return: A dict mapping header names to their values.
        """
        return self._headers.copy()

    @staticmethod
    def _filter_cookies(
        raw_cookies: list[Mapping[str, Any]],
    ) -> dict[str, str]:
        """
        Hook:
        take the raw list of cookie-dicts loaded from storage_state
        and return a simple name -> value mapping.
        """
        return {c["name"]: c["value"] for c in raw_cookies}

    @staticmethod
    async def _response_to_str(
        resp: ClientResponse,
        encoding: str | None = None,
    ) -> str:
        """
        Read the full body of resp as text. Try the provided encoding,
        response charset, and common fallbacks. On failure, fall back
        to utf-8 with errors ignored.
        """
        data: bytes = await resp.read()
        encodings: list[str | None] = [
            encoding,
            resp.charset,
            "gb2312",
            "gb18030",
            "gbk",
            "utf-8",
        ]

        for enc in (e for e in encodings if e is not None):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode(encoding or "utf-8", errors="ignore")

    async def _download_one_image(
        self,
        url: str,
        folder: Path,
        *,
        on_exist: Literal["overwrite", "skip", "rename"],
    ) -> None:
        """Download a single image."""
        save_path = self._build_filepath(
            url=url,
            folder=folder,
            default_suffix=DEFAULT_IMAGE_SUFFIX,
            on_exist=on_exist,
        )
        if save_path.exists() and on_exist == "skip":
            return

        async with await self.get(url) as resp:
            try:
                resp.raise_for_status()
            except aiohttp.ClientResponseError as e:
                self.logger.warning("Skip %s (HTTP %s): %s", url, e.status, e)
                return

            write_file(
                content=await resp.read(),  # bytes
                filepath=save_path,
                on_exist=on_exist,
            )
            self.logger.debug("Saved image: %s <- %s", save_path, url)

    def _resolve_base_url(self, locale_style: str) -> str:
        key = locale_style.strip().lower()
        return self.BASE_URL_MAP.get(key, self.DEFAULT_BASE_URL)

    @staticmethod
    def _build_filepath(
        url: str,
        folder: Path,
        default_suffix: str,
        on_exist: Literal["overwrite", "skip", "rename"],
    ) -> Path:
        parsed_url = urlparse(url)
        url_path = Path(unquote(parsed_url.path))

        raw_name = url_path.name or "unnamed"
        name = sanitize_filename(raw_name)

        if "." not in name and (url_path.suffix or default_suffix):
            name += url_path.suffix or default_suffix

        file_path = folder / name
        if on_exist == "rename":
            file_path = _unique_path(file_path)

        return file_path

    async def __aenter__(self) -> Self:
        if self._session is None or self._session.closed:
            await self.init()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        await self.close()


class GenericSession(BaseSession):
    """
    Generic mid-layer for novel sites.

    Children override constants like:
      * site_name
      * BOOK_INFO_URL / CHAPTER_URL
      * BOOK_CATALOG_URL (optional)
      * BASE_URL (for sites that use relative page suffixes)
      * BASE_URL_MAP / DEFAULT_BASE_URL (when URL depends on variant)
      * BOOK_ID_REPLACEMENTS (e.g. [("-", "/")])

    For paginated info/chapters, set:
      * USE_PAGINATED_INFO = True and implement relative_info_url
      * USE_PAGINATED_CATALOG = True and implement relative_catalog_url
      * USE_PAGINATED_CHAPTER = True and implement relative_chapter_url

    For catalogs:
      * HAS_SEPARATE_CATALOG = True if site has a dedicated catalog page
    """

    BOOK_ID_REPLACEMENTS: list[tuple[str, str]] = []

    # Simple template-style URLs (single page)
    BOOK_INFO_URL: str | None = None
    CHAPTER_URL: str | None = None

    # Optional extra info page ([info, catalog])
    HAS_SEPARATE_CATALOG: bool = False
    BOOK_CATALOG_URL: str | None = None

    # For sites that build full URLs with a BASE_URL + relative suffixes
    BASE_URL: str | None = None

    # Pagination toggles
    USE_PAGINATED_INFO: bool = False
    USE_PAGINATED_CATALOG: bool = False
    USE_PAGINATED_CHAPTER: bool = False

    async def get_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
        book_id = self._transform_book_id(book_id)
        pages: list[str] = []

        # --- 1) Info ---
        if self.USE_PAGINATED_INFO:
            pages = await self._paginate(
                make_suffix=lambda idx: self.relative_info_url(book_id, idx),
                page_type="info",
                book_id=book_id,
                **kwargs,
            )
            if not pages:
                return []
        else:
            info_url = self.book_info_url(base_url=self._base_url, book_id=book_id)
            pages = [await self.fetch(info_url, **kwargs)]

        # --- 2) Catalog ---
        if self.HAS_SEPARATE_CATALOG:
            if self.USE_PAGINATED_CATALOG:
                catalog_pages = await self._paginate(
                    make_suffix=lambda idx: self.relative_catalog_url(book_id, idx),
                    page_type="catalog",
                    book_id=book_id,
                    **kwargs,
                )
                if not catalog_pages:
                    return []
                pages.extend(catalog_pages)

            elif self.BOOK_CATALOG_URL:
                catalog_url = self.book_catalog_url(
                    base_url=self._base_url, book_id=book_id
                )
                pages.append(await self.fetch(catalog_url, **kwargs))

        return pages

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        book_id = self._transform_book_id(book_id)

        if self.USE_PAGINATED_CHAPTER:
            return await self._paginate(
                make_suffix=lambda idx: self.relative_chapter_url(
                    book_id, chapter_id, idx
                ),
                page_type="chapter",
                book_id=book_id,
                chapter_id=chapter_id,
                **kwargs,
            )

        # Single chapter page
        url = self.chapter_url(
            base_url=self._base_url, book_id=book_id, chapter_id=chapter_id
        )
        return [await self.fetch(url, **kwargs)]

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        """
        Return the *relative* URL suffix (prefixed by "/") for the info page #idx.
        """
        raise NotImplementedError(f"{cls.__name__} must implement relative_info_url")

    @classmethod
    def relative_catalog_url(cls, book_id: str, idx: int) -> str:
        """
        Return the *relative* URL suffix (prefixed by "/") for the catalog page #idx.
        """
        raise NotImplementedError(f"{cls.__name__} must implement relative_catalog_url")

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        """
        Return the *relative* URL suffix (prefixed by "/") for the chapter page #idx.
        """
        raise NotImplementedError(f"{cls.__name__} must implement relative_chapter_url")

    def should_continue_pagination(
        self,
        current_html: str,
        next_suffix: str,
        next_idx: int,
        page_type: Literal["info", "catalog", "chapter"],
        book_id: str,
        chapter_id: str | None = None,
    ) -> bool:
        return next_suffix in current_html

    def _transform_book_id(self, book_id: str) -> str:
        for old, new in self.BOOK_ID_REPLACEMENTS:
            book_id = book_id.replace(old, new)
        return book_id

    async def _paginate(
        self,
        *,
        make_suffix: Callable[[int], str],
        page_type: Literal["info", "catalog", "chapter"],
        book_id: str,
        chapter_id: str | None = None,
        **fetch_kwargs: Any,
    ) -> list[str]:
        """
        Generic pagination loop for info/catalog/chapter.

        Starts at idx=1 and continues while should_continue_pagination(...) is True.
        """
        if not self.BASE_URL:
            raise RuntimeError(
                f"{self.site_name}: BASE_URL is required for {page_type}"
            )
        origin = self.BASE_URL.rstrip("/")

        pages: list[str] = []
        idx = 1
        suffix = make_suffix(idx)

        while True:
            html = await self.fetch(origin + suffix, **fetch_kwargs)
            pages.append(html)
            idx += 1
            suffix = make_suffix(idx)
            if not self.should_continue_pagination(
                current_html=html,
                next_suffix=suffix,
                next_idx=idx,
                page_type=page_type,
                book_id=book_id,
                chapter_id=chapter_id,
            ):
                break
            await self._sleep()

        return pages

    @classmethod
    def book_info_url(cls, **kwargs: Any) -> str:
        if not cls.BOOK_INFO_URL:
            raise NotImplementedError(f"{cls.__name__}.BOOK_INFO_URL not set")
        return cls.BOOK_INFO_URL.format(**kwargs)

    @classmethod
    def book_catalog_url(cls, **kwargs: Any) -> str:
        if not cls.BOOK_CATALOG_URL:
            raise NotImplementedError(f"{cls.__name__}.BOOK_CATALOG_URL not set")
        return cls.BOOK_CATALOG_URL.format(**kwargs)

    @classmethod
    def chapter_url(cls, **kwargs: Any) -> str:
        if not cls.CHAPTER_URL:
            raise NotImplementedError(f"{cls.__name__}.CHAPTER_URL not set")
        return cls.CHAPTER_URL.format(**kwargs)
