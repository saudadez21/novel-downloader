#!/usr/bin/env python3
"""
novel_downloader.plugins.base.fetcher
-------------------------------------

Abstract base class providing common HTTP session handling for fetchers.
"""

import abc
import asyncio
import logging
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, Self

from novel_downloader.infra.http_defaults import DEFAULT_USER_HEADERS, IMAGE_HEADERS
from novel_downloader.infra.sessions import create_session
from novel_downloader.libs.filesystem import font_filename, image_filename, write_file
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.utils.rate_limiter import TokenBucketRateLimiter
from novel_downloader.schemas import FetcherConfig, LoginField, MediaResource

logger = logging.getLogger(__name__)


class BaseFetcher(abc.ABC):
    """
    BaseFetcher wraps basic HTTP operations.
    """

    site_name: str
    BASE_URL_MAP: dict[str, str] = {}
    DEFAULT_BASE_URL: str = ""
    IMAGE_HEADERS: dict[str, str] = IMAGE_HEADERS

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
        self._is_logged_in = False

        self._cache_dir = Path(config.cache_dir) / self.site_name

        self.session = create_session(
            backend=config.backend,
            cfg=config,
            cookies=cookies,
            **kwargs,
        )

        self._rate_limiter: TokenBucketRateLimiter | None = (
            TokenBucketRateLimiter(config.max_rps) if config.max_rps > 0 else None
        )

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """"""
        await self.session.init()

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        await self.session.close()

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
        if not cookies:
            return False
        self.session.update_cookies(cookies)

        self._is_logged_in = await self._check_login_status()
        return self._is_logged_in

    @abc.abstractmethod
    async def fetch_book_info(
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
    async def fetch_chapter_content(
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

    async def fetch_data(self, url: str, **kwargs: Any) -> bytes | None:
        """
        Fetch arbitrary binary data from a remote URL.

        :param url: The target URL.
        :return: raw content if success, else None
        """
        try:
            resp = await self.session.get(url, **kwargs)
        except Exception as e:
            logger.warning(
                "Request failed (site=%s) %s: %s",
                self.site_name,
                url,
                e,
            )
            return None

        if not resp.ok:
            logger.warning(
                "Request failed (site=%s) %s: HTTP %s",
                self.site_name,
                url,
                resp.status,
            )
            return None

        if not resp.content:
            logger.warning(
                "Empty response (site=%s): %s",
                self.site_name,
                url,
            )
            return None

        return resp.content

    async def fetch_media(
        self,
        media_dir: Path,
        resources: list[MediaResource],
        *,
        on_exist: Literal["overwrite", "skip"] = "skip",
        concurrent: int = 5,
    ) -> None:
        """
        Process and persist a list of media resources asynchronously.

        :param media_dir: Destination directory.
        :param resources: List of :class:`MediaResource` items.
        :param on_exist: Behavior when existing files are found.
        :param concurrent: Number of concurrent tasks per batch.
        """
        if not resources:
            return

        media_dir.mkdir(parents=True, exist_ok=True)

        img_urls: list[str] = []
        font_urls: list[str] = []

        for res in resources:
            url = res.get("url")
            if not url:
                continue

            r_type = res.get("type")
            if r_type == "image":
                img_urls.append(url)
            elif r_type == "font":
                font_urls.append(url)

        if img_urls:
            await self.fetch_images(
                media_dir,
                img_urls,
                on_exist=on_exist,
                concurrent=concurrent,
            )

        if font_urls:
            await self.fetch_fonts(
                media_dir,
                font_urls,
                on_exist=on_exist,
                concurrent=concurrent,
            )

    async def fetch_image(
        self,
        url: str,
        img_dir: Path,
        *,
        name: str | None = None,
        on_exist: Literal["overwrite", "skip"] = "skip",
    ) -> Path | None:
        """
        Download a single image and return its saved path.

        :param url: Image URL.
        :param img_dir: Destination folder.
        :param name: Optional explicit filename (without suffix).
        :param on_exist: What to do when file exists.
        :return: Path of saved image, or None if failed/skipped.
        """
        img_dir.mkdir(parents=True, exist_ok=True)
        return await self._fetch_one_image(url, img_dir, name=name, on_exist=on_exist)

    async def fetch_images(
        self,
        img_dir: Path,
        urls: list[str],
        *,
        on_exist: Literal["overwrite", "skip"] = "skip",
        concurrent: int = 5,
    ) -> None:
        """
        Download images to `img_dir` in batches.

        Any HTTP error (raise_for_status) is logged and skipped.

        :param img_dir: Destination folder.
        :param urls: List of image URLs (http/https).
        :param on_exist: What to do when file exists.
        :param concurrent: Concurrency per batch.
        """
        if not urls:
            return

        img_dir.mkdir(parents=True, exist_ok=True)

        batch_size = max(1, concurrent)
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            tasks = [
                self._fetch_one_image(url, img_dir, on_exist=on_exist) for url in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.warning("Image download error: %s", r)

    async def fetch_fonts(
        self,
        font_dir: Path,
        urls: list[str],
        *,
        on_exist: Literal["overwrite", "skip"] = "skip",
        concurrent: int = 5,
    ) -> None:
        """Download fonts to `font_dir` in batches."""
        if not urls:
            return

        font_dir.mkdir(parents=True, exist_ok=True)

        batch_size = max(1, concurrent)
        for i in range(0, len(urls), batch_size):
            batch = urls[i : i + batch_size]
            tasks = [
                self._fetch_one_font(url, font_dir, on_exist=on_exist) for url in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.warning("Font download error: %s", r)

    async def load_state(self) -> bool:
        """
        Load session cookies from a file to restore previous login state.

        :return: True if the session state was loaded, False otherwise.
        """
        self.session.load_cookies(self._cache_dir)

        self._is_logged_in = await self._check_login_status()
        return self._is_logged_in

    async def save_state(self) -> bool:
        """
        Save the current session cookies to a file for future reuse.

        :return: True if the session state was saved, False otherwise.
        """
        return self.session.save_cookies(self._cache_dir)

    @property
    def is_logged_in(self) -> bool:
        """
        Indicates whether the requester is currently authenticated.
        """
        return self._is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="cookies",
                label="Cookie",
                type="cookie",
                required=True,
                placeholder="Paste your login cookies here",
                description="Copy the cookies from your browser's developer tools while logged in.",  # noqa: E501
            ),
        ]

    async def fetch(
        self,
        url: str,
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> str:
        """
        Fetch the content from the given URL asynchronously, with retry support.

        :param url: The target URL to fetch.
        :param kwargs: Additional keyword arguments to pass to `session.get`.
        :return: The response body as text.
        """
        if self._rate_limiter:
            await self._rate_limiter.wait()

        for attempt in range(self._retry_times + 1):
            resp = await self.session.get(url, encoding=encoding, **kwargs)
            if not resp.ok:
                if attempt < self._retry_times:
                    await async_jitter_sleep(
                        self._backoff_factor,
                        mul_spread=1.1,
                        max_sleep=self._backoff_factor + 2,
                    )
                    continue
                raise ConnectionError(
                    f"Request to {url} failed with status {resp.status}"
                )
            return resp.text

        raise RuntimeError("Unreachable code reached in fetch()")

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        return True

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
        return self.session.headers

    async def _fetch_one_image(
        self,
        url: str,
        folder: Path,
        *,
        name: str | None = None,
        on_exist: Literal["overwrite", "skip"],
    ) -> Path | None:
        """Download a single image and save with a hashed filename."""
        save_path = folder / image_filename(url, name=name)

        if save_path.exists() and on_exist == "skip":
            logger.debug("Skip existing image: %s", save_path)
            return save_path

        content = await self.fetch_data(url, headers=self.IMAGE_HEADERS)
        if content is None:
            return None

        write_file(content=content, filepath=save_path, on_exist="overwrite")
        logger.debug("Saved image: %s <- %s", save_path, url)
        return save_path

    async def _fetch_one_font(
        self,
        url: str,
        folder: Path,
        *,
        name: str | None = None,
        on_exist: Literal["overwrite", "skip"],
    ) -> Path | None:
        """Download a single font and save with a hashed filename."""
        save_path = folder / font_filename(url, name=name)

        if save_path.exists() and on_exist == "skip":
            logger.debug("Skip existing font: %s", save_path)
            return save_path

        content = await self.fetch_data(url, headers=DEFAULT_USER_HEADERS)
        if content is None:
            return None

        write_file(content=content, filepath=save_path, on_exist="overwrite")
        logger.debug("Saved font: %s <- %s", save_path, url)
        return save_path

    def _resolve_base_url(self, locale_style: str) -> str:
        key = locale_style.strip().lower()
        return self.BASE_URL_MAP.get(key, self.DEFAULT_BASE_URL)

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


class GenericFetcher(BaseFetcher):
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
    CHAP_ID_REPLACEMENTS: list[tuple[str, str]] = []

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

    async def fetch_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
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

    async def fetch_chapter_content(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        book_id = self._transform_book_id(book_id)
        chapter_id = self._transform_chap_id(chapter_id)

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

    def _transform_chap_id(self, chap_id: str) -> str:
        for old, new in self.CHAP_ID_REPLACEMENTS:
            chap_id = chap_id.replace(old, new)
        return chap_id

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
