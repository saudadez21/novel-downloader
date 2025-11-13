#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins.download
----------------------------------------
"""

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Final, Protocol, final

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.schemas import BookConfig, BookInfoDict, ChapterDict

ONE_DAY = 86400  # seconds
logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from novel_downloader.plugins.protocols import (
        DownloadUI,
        _ClientContext,
    )

    class DownloadClientContext(_ClientContext, Protocol):
        """"""

        async def get_book_info(
            self,
            book_id: str,
            **kwargs: Any,
        ) -> BookInfoDict:
            ...

        async def get_chapter(
            self,
            chapter_id: str,
            book_id: str | None = None,
        ) -> ChapterDict | None:
            ...

        async def _dl_cache_info_images(
            self, book_id: str, book_info: BookInfoDict
        ) -> None:
            ...

        async def _dl_fix_chapter_ids(
            self,
            book_id: str,
            book_info: BookInfoDict,
            storage: ChapterStorage,
        ) -> BookInfoDict:
            ...

        def _dl_check_restricted(self, html_list: list[str]) -> bool:
            ...

        def _dl_check_empty(self, raw_pages: list[str]) -> bool:
            ...

        def _dl_check_refetch(self, chap: ChapterDict) -> bool:
            ...


@final
class StopToken:
    """Typed sentinel used to end queues."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "STOP"


STOP: Final[StopToken] = StopToken()


class DownloadMixin:
    """"""

    async def download_book(
        self: "DownloadClientContext",
        book: BookConfig,
        *,
        ui: "DownloadUI | None" = None,
        **kwargs: Any,
    ) -> None:
        """
        Download all chapters and metadata for a single book.

        :param book: :class:`BookConfig` with at least ``book_id`` defined.
        :param ui: Optional :class:`DownloadUI` for progress reporting.
        """
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        if ui:
            await ui.on_start(book)

        # ---- metadata ---
        book_info = await self.get_book_info(book_id=book_id)
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            book_info = await self._dl_fix_chapter_ids(
                book_id,
                book_info,
                storage,
            )

        await self._dl_cache_info_images(book_id, book_info)

        vols = book_info["volumes"]
        plan = self._extract_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return

        total = len(plan)
        done = 0

        async def bump(n: int = 1) -> None:
            nonlocal done
            done += n
            if ui:
                await ui.on_progress(done, total)

        # ---- queues & batching ---
        save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue(maxsize=10)
        batches: dict[bool, list[ChapterDict]] = {False: [], True: []}
        sem = asyncio.Semaphore(self.workers)

        def _batch(need_refetch: bool) -> list[ChapterDict]:
            return batches[need_refetch]

        async def flush_batch(need_refetch: bool) -> None:
            batch = _batch(need_refetch)
            if not batch:
                return
            try:
                # need_refetch=True for encrypted, False for plain
                storage.upsert_chapters(batch, need_refetch=need_refetch)
            except Exception as e:
                logger.error(
                    "Storage batch upsert failed (site=%s, book=%s, size=%d, need_refetch=%s): %s",  # noqa: E501
                    self._site,
                    book_id,
                    len(batch),
                    need_refetch,
                    e,
                )
            else:
                await bump(len(batch))
            finally:
                batch.clear()

        async def flush_all() -> None:
            await flush_batch(False)
            await flush_batch(True)

        # ---- workers ---
        async def storage_worker() -> None:
            while True:
                item = await save_q.get()
                if isinstance(item, StopToken):
                    break

                need = self._dl_check_refetch(item)
                bucket = _batch(need)
                bucket.append(item)
                if len(bucket) >= self._storage_batch_size:
                    await flush_batch(need)
            await flush_all()

        async def producer(cid: str) -> None:
            async with sem:
                if self._skip_existing and not storage.need_refetch(cid):
                    await bump(1)
                    return

                chap = await self.get_chapter(book_id, cid)
                if chap is not None:
                    await save_q.put(chap)

                await async_jitter_sleep(
                    base=self._request_interval,
                    mul_spread=1.1,
                    max_sleep=self._request_interval + 2,
                )

        # ---- run tasks ---
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            storage_task = asyncio.create_task(storage_worker())

            try:
                tasks = [asyncio.create_task(producer(cid)) for cid in plan]
                await asyncio.gather(*tasks)

                # signal storage to finish and wait for flush
                await save_q.put(STOP)
                await storage_task
            except asyncio.CancelledError:
                logger.info("Download cancelled, stopping storage worker...")
                await save_q.put(STOP)

                try:
                    await asyncio.wait_for(storage_task, timeout=10)
                except TimeoutError:
                    logger.warning("Storage worker did not exit, cancelling.")
                    storage_task.cancel()
                    await asyncio.gather(storage_task, return_exceptions=True)

                raise
            finally:
                if not storage_task.done():
                    storage_task.cancel()
                    await asyncio.gather(storage_task, return_exceptions=True)

        # ---- done ---
        if ui:
            await ui.on_complete(book)

        logger.info(
            "Download completed for site=%s book=%s",
            self._site,
            book_id,
        )

    async def download_chapter(
        self: "DownloadClientContext",
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> None:
        """
        Download a specific chapter by its identifier.

        :param book_id: Book identifier.
        :param chapter_id: Identifier of the chapter to download.
        """
        # TODO: placeholder
        return

    async def cache_medias(
        self: "DownloadClientContext",
        book: BookConfig,
        *,
        force_update: bool = False,
        concurrent: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Asynchronously pre-cache all images associated with a book.

        :param book: The BookConfig instance representing the book.
        :param force_update: If True, re-download even if images are already cached.
        :param concurrent: Maximum number of concurrent download tasks.
        """
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)
        img_dir = raw_base / "medias"

        # ---- metadata ---
        book_info = self._load_book_info(book_id=book_id)
        await self._dl_cache_info_images(book_id, book_info)

        vols = book_info["volumes"]
        plan = self._extract_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return

        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            chapters = storage.get_chapters(plan)
            for chap in chapters.values():
                if chap is None:
                    continue

                imgs = self._extract_image_urls(chap)
                await self.fetcher.fetch_images(
                    img_dir,
                    imgs,
                    on_exist="overwrite" if force_update else "skip",
                    concurrent=concurrent,
                )

    async def get_book_info(
        self: "DownloadClientContext",
        book_id: str,
        **kwargs: Any,
    ) -> BookInfoDict:
        """
        Attempt to fetch and parse the book_info for a given book_id.

        :param book_id: identifier of the book
        :return: parsed BookInfoDict
        """
        book_info: BookInfoDict | None = None
        try:
            book_info = self._load_book_info(book_id)
            if book_info and time.time() - book_info.get("last_checked", 0.0) < ONE_DAY:
                return book_info
        except FileNotFoundError as exc:
            logger.debug("No cached book_info found for %s: %s", book_id, exc)
        except Exception as exc:
            logger.info("Failed to load cached book_info for %s: %s", book_id, exc)

        try:
            info_html = await self.fetcher.fetch_book_info(book_id)
            self._save_raw_pages(book_id, "info", info_html)

            book_info = self.parser.parse_book_info(info_html)
            if book_info:
                book_info["last_checked"] = time.time()
                self._save_book_info(book_id, book_info)
                return book_info

        except Exception as exc:
            logger.warning("Failed to fetch/parse book_info for %s: %s", book_id, exc)

        if book_info is None:
            raise LookupError(f"Unable to load book_info for {book_id}")

        return book_info

    async def get_chapter(
        self: "DownloadClientContext",
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> "ChapterDict | None":
        """
        Fetch, parse, and return a single chapter, retrying on transient errors.

        :param book_id: Book identifier.
        :param chapter_id: Chapter identifier.
        :return: Parsed :class:`ChapterDict`, or ``None`` if failed.
        """
        for attempt in range(self._retry_times + 1):
            try:
                raw_pages = await self.fetcher.fetch_chapter_content(
                    book_id, chapter_id
                )
                self._save_raw_pages(book_id, chapter_id, raw_pages)

                if self._dl_check_restricted(raw_pages):
                    logger.warning(
                        "Access limited (site=%s, book=%s, chapter=%s)",
                        self._site,
                        book_id,
                        chapter_id,
                    )
                    return None

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter_content, raw_pages, chapter_id
                )
                if not chap:
                    if self._dl_check_empty(raw_pages):
                        logger.warning(
                            "Empty parse result (site=%s, book=%s, chapter=%s)",
                            self._site,
                            book_id,
                            chapter_id,
                        )
                        return None
                    raise ValueError("Empty parse result")

                imgs = self._extract_image_urls(chap)
                img_dir = self._raw_data_dir / book_id / "medias"
                await self.fetcher.fetch_images(img_dir, imgs)
                return chap
            except Exception as e:
                if attempt < self._retry_times:
                    logger.info(
                        "Retrying (site=%s, book=%s, chapter=%s, attempt=%d): %s",
                        self._site,
                        book_id,
                        chapter_id,
                        attempt + 1,
                        e,
                    )
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    logger.warning(
                        "Failed chapter (site=%s, book=%s, chapter=%s): %s",
                        self._site,
                        book_id,
                        chapter_id,
                        e,
                    )
        return None

    async def _dl_fix_chapter_ids(
        self: "DownloadClientContext",
        book_id: str,
        book_info: BookInfoDict,
        storage: ChapterStorage,
    ) -> BookInfoDict:
        """
        Repair missing ``chapterId`` fields in the given book's metadata.

        This method attempts to infer missing chapter IDs by loading the
        previous chapter (from local storage or by refetching) and reading
        its ``extra.next_cid`` field.

        Refetched chapters are cached via the provided storage instance.
        """
        prev_cid: str = ""
        for vol in book_info["volumes"]:
            for chap in vol["chapters"]:
                cid = chap.get("chapterId")
                if cid:
                    prev_cid = cid
                    continue

                if not prev_cid:
                    continue

                # missing id: try storage
                data = storage.get_chapter(prev_cid)
                if not data:
                    # fetch+parse previous to discover next
                    data = await self.get_chapter(book_id, prev_cid)
                    if not data:
                        logger.warning(
                            "Failed to fetch chapter (site=%s, book=%s, prev=%s) during repair",  # noqa: E501
                            self._site,
                            book_id,
                            prev_cid,
                        )
                        continue
                    storage.upsert_chapter(data)
                    await async_jitter_sleep(
                        self._request_interval,
                        mul_spread=1.1,
                        max_sleep=self._request_interval + 2,
                    )

                next_cid = data.get("extra", {}).get("next_cid")
                if not next_cid:
                    logger.warning(
                        "No next_cid (site=%s, book=%s, prev=%s)",
                        self._site,
                        book_id,
                        prev_cid,
                    )
                    continue

                logger.info(
                    "Repaired chapterId (site=%s, book=%s): %s <- %s",
                    self._site,
                    book_id,
                    next_cid,
                    prev_cid,
                )
                chap["chapterId"] = next_cid
                prev_cid = next_cid

        self._save_book_info(book_id, book_info)
        return book_info

    async def _dl_cache_info_images(
        self: "DownloadClientContext",
        book_id: str,
        book_info: BookInfoDict,
    ) -> None:
        """
        Download cover and volume images for a book.

        :param book_id: Unique ID of the book.
        :param book_info: Metadata dictionary containing cover URLs.
        """
        img_dir = self._raw_data_dir / book_id / "medias"
        img_dir.mkdir(parents=True, exist_ok=True)

        # --- cover image ---
        if cover_url := book_info.get("cover_url"):
            await self.fetcher.fetch_image(cover_url, img_dir, name="cover")

        # --- volume covers ---
        vol_covers = [
            cover
            for v in book_info.get("volumes", [])
            if (cover := v.get("volume_cover"))
        ]
        if vol_covers:
            await self.fetcher.fetch_images(img_dir, vol_covers)

    def _dl_check_restricted(self, html_list: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. login required, paywall, VIP, subscription, etc.)

        :param html_list: List of raw HTML strings.
        """
        return False

    def _dl_check_empty(self, raw_pages: list[str]) -> bool:
        """
        Return True if parse_chapter returns empty but should be skipped.
        """
        return False

    def _dl_check_refetch(self, chap: ChapterDict) -> bool:
        """Override this hook to decide if a chapter needs refetch."""
        return False
