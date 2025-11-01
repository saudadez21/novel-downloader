#!/usr/bin/env python3
"""
novel_downloader.plugins.common.client
--------------------------------------
"""

import asyncio
import json
import time
from collections.abc import Sequence
from html import escape
from pathlib import Path
from typing import Any, Final, Protocol, cast, final

from novel_downloader.infra.paths import CSS_MAIN_PATH
from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.epub import (
    Chapter,
    EpubBuilder,
    StyleSheet,
    Volume,
)
from novel_downloader.libs.filesystem import img_name, sanitize_filename, write_file
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.client import BaseClient
from novel_downloader.plugins.protocols import (
    DownloadUI,
    ExportUI,
    LoginUI,
    ProcessUI,
)
from novel_downloader.plugins.utils.stage_runner import StageRunner
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    ExporterConfig,
    ProcessorConfig,
    VolumeInfoDict,
)


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class _ExportFunc(Protocol):
    def __call__(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        stage: str | None,
        **kwargs: Any,
    ) -> list[Path]:
        ...


@final
class StopToken:
    """Typed sentinel used to end queues."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "STOP"


STOP: Final[StopToken] = StopToken()
ONE_DAY = 86400  # seconds


class CommonClient(BaseClient):
    """
    Specialized client for "common" novel sites.
    """

    _IMAGE_WRAPPER = '<div class="duokan-image-single illus">{img}</div>'

    async def login(
        self,
        *,
        ui: LoginUI,
        login_cfg: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
        """
        if await self.fetcher.load_state():
            return True

        login_data = await ui.prompt(self.fetcher.login_fields, prefill=login_cfg)
        if not await self.fetcher.login(**login_data):
            if ui:
                ui.on_login_failed()
            return False

        await self.fetcher.save_state()
        if ui:
            ui.on_login_success()
        return True

    async def download(
        self,
        book: BookConfig,
        *,
        ui: DownloadUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book.

        :param book: BookConfig with at least 'book_id'.
        :param ui: Optional DownloadUI to report progress or messages.
        """
        if ui:
            await ui.on_start(book)

        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        # ---- metadata ---
        book_info = await self._get_book_info(book_id=book_id)
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            book_info = await self._repair_chapter_ids(
                book_id,
                book_info,
                storage,
            )

        await self._download_info_images(book_id, book_info)

        vols = book_info["volumes"]
        plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            self.logger.info(
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
                self.logger.error(
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

                need = self._need_refetch(item)
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

                chap = await self._process_chapter(book_id, cid)
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
                self.logger.info("Download cancelled, stopping storage worker...")
                await save_q.put(STOP)

                try:
                    await asyncio.wait_for(storage_task, timeout=10)
                except TimeoutError:
                    self.logger.warning("Storage worker did not exit, cancelling.")
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

        self.logger.info(
            "Download completed for site=%s book=%s",
            self._site,
            book_id,
        )

    def process(
        self,
        book: BookConfig,
        processors: list[ProcessorConfig],
        *,
        ui: ProcessUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Run all processors for a single book.

        :param book: BookConfig to process.
        :param ui: Optional ProcessUI to report progress.
        """
        book_id = self._normalize_book_id(book.book_id)
        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        raw_sqlite = raw_base / "chapter.raw.sqlite"
        book_info_path = raw_base / "book_info.raw.json"

        # Pre-flight checks
        if not raw_sqlite.is_file():
            if ui:
                ui.on_missing(book, "raw", raw_sqlite)
            return
        if not book_info_path.is_file():
            if ui:
                ui.on_missing(book, "book_info", book_info_path)
            return

        stage_name: str = "Unknown"
        try:
            runner = StageRunner(base_dir=raw_base, book=book)
            for pconf in processors:
                stage_name = pconf.name
                if ui:
                    ui.on_stage_start(book, stage_name)

                def _progress(
                    done: int,
                    total: int,
                    *,
                    _b: BookConfig = book,
                    _s: str = stage_name,
                ) -> None:
                    if ui:
                        ui.on_stage_progress(_b, _s, done, total)

                runner.run(pconf, on_progress=_progress)

                if ui:
                    ui.on_stage_complete(book, stage_name)

            self.logger.info("All stages completed successfully for book %s", book_id)

        except Exception as e:
            self.logger.warning(
                "Processing failed at stage '%s' for book %s: %s",
                stage_name,
                book_id,
                e,
            )

    async def cache_images(
        self,
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
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)
        img_dir = raw_base / "images"

        # ---- metadata ---
        book_info = self._load_book_info(book_id=book_id)
        await self._download_info_images(book_id, book_info)

        vols = book_info["volumes"]
        plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return

        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            chapters = storage.get_chapters(plan)
            for chap in chapters.values():
                if chap is None:
                    continue

                imgs = self._extract_img_urls(chap["extra"])
                await self.fetcher.download_images(
                    img_dir,
                    imgs,
                    batch_size=concurrent,
                    on_exist="overwrite" if force_update else "skip",
                )

    def export(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        ui: ExportUI | None = None,
        **kwargs: Any,
    ) -> dict[str, list[Path]]:
        """
        Persist the assembled book to disk.

        :param book: The book configuration to export.
        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :param ui: Optional ExportUI for reporting export progress.
        :return: A mapping from format name to the resulting file path.
        """
        formats = formats or ["epub"]
        results: dict[str, list[Path]] = {}

        for fmt in formats:
            method_name = f"export_as_{fmt.lower()}"
            export_func: _ExportFunc | None = getattr(self, method_name, None)

            if not callable(export_func):
                if ui:
                    ui.on_unsupported(book, fmt)
                results[fmt] = []
                continue

            if ui:
                ui.on_start(book, fmt)

            try:
                paths = export_func(book, cfg, stage=stage, **kwargs)
                results[fmt] = paths

                if paths and ui:
                    for path in paths:
                        ui.on_success(book, fmt, path)

            except Exception as e:
                results[fmt] = []
                self.logger.warning(f"Error exporting {fmt}: {e}")
                if ui:
                    ui.on_error(book, fmt, e)

        return results

    def export_as_txt(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """
        Export a novel as a single text file by merging all chapter data.
        """
        cfg = cfg or ExporterConfig()
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        stage = stage or self._resolve_stage_selection(book_id)
        book_info = self._load_book_info(book_id, stage=stage)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return []

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""
        header_txt = self._build_txt_header(book_info, name, author)

        # --- Build body by volumes & chapters ---
        parts: list[str] = [header_txt]
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, volume in enumerate(vols, start=1):
                vol_title = volume.get("volume_name") or f"卷 {v_idx}"
                parts.append(self._build_txt_volume_heading(vol_title, volume))

                # Collect chapter ids then batch fetch
                cids = [
                    c["chapterId"]
                    for c in volume.get("chapters", [])
                    if c.get("chapterId")
                ]
                if not cids:
                    continue
                chap_map = storage.get_chapters(cids)
                for ch_info in volume.get("chapters", []):
                    cid = ch_info.get("chapterId")
                    ch_title = ch_info.get("title")
                    if not cid:
                        continue

                    ch = chap_map.get(cid)
                    if not ch:
                        continue

                    parts.append(self._build_txt_chapter(ch_title, ch))

        final_text = "\n".join(parts)

        # --- Determine output file path ---
        out_name = self._get_filename(
            cfg.filename_template,
            title=name,
            author=author,
            ext="txt",
        )
        out_path = self._output_dir / sanitize_filename(out_name)

        # --- Save final text ---
        try:
            result = write_file(
                content=final_text, filepath=out_path, on_exist="overwrite"
            )
            self.logger.info(
                "Exported TXT (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            self.logger.error(
                "Failed to write TXT (site=%s, book=%s) to %s: %s",
                self._site,
                book_id,
                out_path,
                e,
            )
            return []

        return [result]

    def export_as_epub(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        cfg = cfg or ExporterConfig()
        mode = cfg.split_mode
        if mode == "book":
            return self._export_epub_by_book(
                book,
                cfg,
                stage=stage,
                **kwargs,
            )
        if mode == "volume":
            return self._export_epub_by_volume(
                book,
                cfg,
                stage=stage,
                **kwargs,
            )
        raise ValueError(f"Unsupported split_mode: {mode!r}")

    def _export_epub_by_volume(
        self,
        book: BookConfig,
        cfg: ExporterConfig,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """
        Export each volume of a novel as a separate EPUB file.
        """
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)
        img_dir: Path | None = None
        if cfg.include_picture:
            img_dir = raw_base / "images"
            img_dir.mkdir(parents=True, exist_ok=True)

        stage = stage or self._resolve_stage_selection(book_id)
        book_info = self._load_book_info(book_id, stage=stage)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return []

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""
        book_summary = book_info.get("summary", "")

        # --- Generate intro + cover ---
        cover_path = self._resolve_img_path(img_dir, book_info.get("cover_url"))

        css_text = CSS_MAIN_PATH.read_text(encoding="utf-8")
        main_css = StyleSheet(id="main_style", content=css_text, filename="main.css")

        # --- Compile columes ---
        outputs: list[Path] = []
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, vol in enumerate(vols, start=1):
                vol_title = vol.get("volume_name") or f"卷 {v_idx}"

                vol_cover = self._resolve_img_path(img_dir, vol.get("volume_cover"))
                vol_cover = vol_cover or cover_path

                epub = EpubBuilder(
                    title=f"{name} - {vol_title}",
                    author=author,
                    description=vol.get("volume_intro") or book_summary,
                    cover_path=vol_cover,
                    subject=book_info.get("tags", []),
                    serial_status=book_info.get("serial_status", ""),
                    word_count=vol.get("word_count", ""),
                    uid=f"{self._site}_{book_id}_v{v_idx}",
                )
                epub.add_stylesheet(main_css)

                # Collect chapter ids then batch fetch
                cids = [
                    c["chapterId"]
                    for c in vol.get("chapters", [])
                    if c.get("chapterId")
                ]
                if not cids:
                    continue
                chap_map = storage.get_chapters(cids)

                # Append each chapter
                seen_cids: set[str] = set()
                for ch_info in vol.get("chapters", []):
                    cid = ch_info.get("chapterId")
                    ch_title = ch_info.get("title")
                    if not cid or cid in seen_cids:
                        continue

                    ch = chap_map.get(cid)
                    if not ch:
                        continue

                    chapter_obj = self._build_epub_chapter(
                        book=epub,
                        css=[main_css],
                        cid=cid,
                        chap_title=ch_title,
                        chap=ch,
                        img_dir=img_dir,
                    )
                    epub.add_chapter(chapter_obj)
                    seen_cids.add(cid)

                out_name = self._get_filename(
                    cfg.filename_template, title=vol_title, author=author, ext="epub"
                )
                out_path = self._output_dir / sanitize_filename(out_name)

                try:
                    outputs.append(epub.export(out_path))
                    self.logger.info(
                        "Exported EPUB (site=%s, book=%s): %s",
                        self._site,
                        book_id,
                        out_path,
                    )
                except Exception as e:
                    self.logger.error(
                        "Failed to write EPUB (site=%s, book=%s) to %s: %s",
                        self._site,
                        book_id,
                        out_path,
                        e,
                    )
        return outputs

    def _export_epub_by_book(
        self,
        book: BookConfig,
        cfg: ExporterConfig,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """
        Export a single novel (identified by `book_id`) to an EPUB file.
        """
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)
        img_dir: Path | None = None
        if cfg.include_picture:
            img_dir = raw_base / "images"
            img_dir.mkdir(parents=True, exist_ok=True)

        stage = stage or self._resolve_stage_selection(book_id)
        book_info = self._load_book_info(book_id, stage=stage)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return []

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""

        # --- Generate intro + cover ---
        cover_path = self._resolve_img_path(
            img_dir, book_info.get("cover_url"), name="cover"
        )

        # --- Initialize EPUB ---
        epub = EpubBuilder(
            title=name,
            author=author,
            description=book_info.get("summary", ""),
            cover_path=cover_path,
            subject=book_info.get("tags", []),
            serial_status=book_info.get("serial_status", ""),
            word_count=book_info.get("word_count", ""),
            uid=f"{self._site}_{book_id}",
        )
        css_text = CSS_MAIN_PATH.read_text(encoding="utf-8")
        main_css = StyleSheet(id="main_style", content=css_text, filename="main.css")
        epub.add_stylesheet(main_css)

        # --- Compile columes ---
        seen_cids: set[str] = set()
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, vol in enumerate(vols, start=1):
                vol_title = vol.get("volume_name") or f"卷 {v_idx}"

                vol_cover = self._resolve_img_path(img_dir, vol.get("volume_cover"))

                curr_vol = Volume(
                    id=f"vol_{v_idx}",
                    title=vol_title,
                    intro=vol.get("volume_intro", ""),
                    cover=vol_cover,
                )

                # Collect chapter ids then batch fetch
                cids = [
                    c["chapterId"]
                    for c in vol.get("chapters", [])
                    if c.get("chapterId")
                ]
                if not cids:
                    epub.add_volume(curr_vol)
                    continue
                chap_map = storage.get_chapters(cids)

                # Append each chapter
                for ch_info in vol.get("chapters", []):
                    cid = ch_info.get("chapterId")
                    ch_title = ch_info.get("title")
                    if not cid or cid in seen_cids:
                        continue

                    ch = chap_map.get(cid)
                    if not ch:
                        continue

                    chapter_obj = self._build_epub_chapter(
                        book=epub,
                        css=[main_css],
                        cid=cid,
                        chap_title=ch_title,
                        chap=ch,
                        img_dir=img_dir,
                    )

                    curr_vol.chapters.append(chapter_obj)
                    seen_cids.add(cid)

                if curr_vol.chapters:
                    epub.add_volume(curr_vol)

        # --- Finalize EPUB ---
        out_name = self._get_filename(
            cfg.filename_template, title=name, author=author, ext="epub"
        )
        out_path = self._output_dir / sanitize_filename(out_name)

        try:
            epub.export(out_path)
            self.logger.info(
                "Exported EPUB (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            self.logger.error(
                "Failed to write EPUB (site=%s, book=%s) to %s: %s",
                self._site,
                book_id,
                out_path,
                e,
            )
            return []
        return [out_path]

    async def _download_info_images(
        self, book_id: str, book_info: BookInfoDict
    ) -> None:
        """
        Download cover and volume images for a book.

        :param book_id: Unique ID of the book.
        :param book_info: Metadata dictionary containing cover URLs.
        """
        img_dir = self._raw_data_dir / book_id / "images"
        img_dir.mkdir(parents=True, exist_ok=True)

        # --- cover image ---
        if cover_url := book_info.get("cover_url"):
            await self.fetcher.download_image(cover_url, img_dir, name="cover")

        # --- volume covers ---
        vol_covers = [
            cover
            for v in book_info.get("volumes", [])
            if (cover := v.get("volume_cover"))
        ]
        if vol_covers:
            await self.fetcher.download_images(img_dir, vol_covers)

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
    ) -> ChapterDict | None:
        """
        Fetches, saves raw HTML, parses a single chapter,
        retrying up to self.retry_times.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self._retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                self._save_html_pages(book_id, cid, html_list)

                if self._is_access_limited(html_list):
                    self.logger.warning(
                        "Access limited (site=%s, book=%s, chapter=%s)",
                        self._site,
                        book_id,
                        cid,
                    )
                    return None

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if not chap:
                    if self._skip_empty_chapter(html_list):
                        self.logger.warning(
                            "Empty parse result (site=%s, book=%s, chapter=%s)",
                            self._site,
                            book_id,
                            cid,
                        )
                        return None
                    raise ValueError("Empty parse result")

                imgs = self._extract_img_urls(chap["extra"])
                img_dir = self._raw_data_dir / book_id / "images"
                await self.fetcher.download_images(img_dir, imgs)
                return chap
            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info(
                        "Retrying (site=%s, book=%s, chapter=%s, attempt=%d): %s",
                        self._site,
                        book_id,
                        cid,
                        attempt + 1,
                        e,
                    )
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning(
                        "Failed chapter (site=%s, book=%s, chapter=%s): %s",
                        self._site,
                        book_id,
                        cid,
                        e,
                    )
        return None

    async def _get_book_info(self, book_id: str) -> BookInfoDict:
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
            self.logger.debug("No cached book_info found for %s: %s", book_id, exc)
        except Exception as exc:
            self.logger.info("Failed to load cached book_info for %s: %s", book_id, exc)

        try:
            info_html = await self.fetcher.get_book_info(book_id)
            self._save_html_pages(book_id, "info", info_html)

            book_info = self.parser.parse_book_info(info_html)
            if book_info:
                book_info["last_checked"] = time.time()
                self._save_book_info(book_id, book_info)
                return book_info

        except Exception as exc:
            self.logger.warning(
                "Failed to fetch/parse book_info for %s: %s", book_id, exc
            )

        if book_info is None:
            raise LookupError(f"Unable to load book_info for {book_id}")

        return book_info

    def _save_book_info(
        self, book_id: str, book_info: BookInfoDict, stage: str = "raw"
    ) -> None:
        """
        Serialize and save the book_info dict as json.

        :param book_id: identifier of the book
        :param book_info: dict containing metadata about the book
        """
        target_dir = self._raw_data_dir / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / f"book_info.{stage}.json").write_text(
            json.dumps(book_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_book_info(self, book_id: str, stage: str = "raw") -> BookInfoDict:
        """
        Load and return the book_info payload for the given book.

        :param book_id: Book identifier.
        :raises FileNotFoundError: if the metadata file does not exist.
        :raises ValueError: if the JSON is invalid or has an unexpected structure.
        :return: Parsed BookInfoDict.
        """
        info_path = self._raw_data_dir / book_id / f"book_info.{stage}.json"
        if not info_path.is_file():
            raise FileNotFoundError(f"Missing metadata file: {info_path}")

        try:
            data = json.loads(info_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupt JSON in {info_path}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(
                f"Invalid JSON structure in {info_path}: expected an object at the top"
            )

        return cast(BookInfoDict, data)

    def _save_html_pages(
        self,
        book_id: str,
        filename: str,
        html_list: Sequence[str],
        *,
        folder: str = "html",
    ) -> None:
        """
        If save_html is enabled, write each HTML snippet to a file.

        Filenames will be {book_id}_{filename}_{index}.html in html_dir.

        :param book_id: The book identifier
        :param filename: used as filename prefix
        :param html_list: list of HTML strings to save
        """
        if not self._save_html:
            return
        html_dir = self._debug_dir / folder
        html_dir.mkdir(parents=True, exist_ok=True)
        for i, html in enumerate(html_list):
            (html_dir / f"{book_id}_{filename}_{i}.html").write_text(
                html, encoding="utf-8"
            )

    def _get_filename(
        self,
        filename_template: str,
        *,
        title: str,
        author: str | None = None,
        append_timestamp: bool = True,
        ext: str = "txt",
        **extra_fields: str,
    ) -> str:
        """
        Generate a filename based on the configured template and metadata fields.

        :param title: Book title (required).
        :param author: Author name (optional).
        :param ext: File extension (e.g., "txt", "epub").
        :param extra_fields: Any additional fields used in the filename template.
        :return: Formatted filename with extension.
        """
        context = SafeDict(title=title, author=author or "", **extra_fields)
        name = filename_template.format_map(context)
        if append_timestamp:
            from datetime import datetime

            name += f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return f"{name}.{ext}"

    def _extract_img_urls(self, extra: dict[str, Any]) -> list[str]:
        """
        Extract all image URLs from 'extra' field.
        """
        if not isinstance(extra, dict):
            return []

        image_positions = extra.get("image_positions")
        if not isinstance(image_positions, dict):
            return []

        urls: list[str] = []
        for line_no, urls_in_line in image_positions.items():
            if not isinstance(urls_in_line, list | tuple):
                self.logger.debug(
                    "image_positions[%r] expected list/tuple, got %r",
                    line_no,
                    type(urls_in_line),
                )
                continue
            for url in urls_in_line:
                if isinstance(url, str) and url.startswith("http"):
                    urls.append(url)
                else:
                    self.logger.debug(
                        "Invalid image URL type or format at line %r: %r",
                        line_no,
                        url,
                    )

        return urls

    async def _repair_chapter_ids(
        self,
        book_id: str,
        book_info: BookInfoDict,
        storage: ChapterStorage,
    ) -> BookInfoDict:
        """
        Fill in missing chapterId fields by retrieving the previous chapter
        and following its 'next_cid'. Uses storage to avoid refetching.
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
                    data = await self._process_chapter(book_id, prev_cid)
                    if not data:
                        self.logger.warning(
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
                    self.logger.warning(
                        "No next_cid (site=%s, book=%s, prev=%s)",
                        self._site,
                        book_id,
                        prev_cid,
                    )
                    continue

                self.logger.info(
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

    @staticmethod
    def _select_chapter_ids(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: set[str],
    ) -> list[str]:
        seen_start = start_id is None
        out: list[str] = []
        for vol in vols:
            for chap in vol["chapters"]:
                cid = chap.get("chapterId")
                if not cid:
                    continue
                if not seen_start:
                    if cid == start_id:
                        seen_start = True
                    else:
                        continue
                if cid not in ignore and chap.get("accessible", True):
                    out.append(cid)
                if end_id is not None and cid == end_id:
                    return out
        return out

    @staticmethod
    def _filter_volumes(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: set[str],
    ) -> list[VolumeInfoDict]:
        """
        Rebuild volumes to include only chapters within
        the [start_id, end_id] range (inclusive),
        while excluding any chapter IDs in `ignore`.

        :param vols: List of volume dicts.
        :param start_id: Range start chapter ID (inclusive) or None to start.
        :param end_id: Range end chapter ID (inclusive) or None to go till the end.
        :param ignore: Set of chapter IDs to exclude (regardless of range).
        :return: New list of volumes with chapters filtered accordingly.
        """
        if start_id is None and end_id is None and not ignore:
            return vols

        started = start_id is None
        finished = False
        result: list[VolumeInfoDict] = []

        for vol in vols:
            if finished:
                break

            kept: list[ChapterInfoDict] = []

            for ch in vol.get("chapters", []):
                cid = ch.get("chapterId")
                if not cid:
                    continue

                # wait until hit the start_id
                if not started:
                    if cid == start_id:
                        started = True
                    else:
                        continue

                if cid not in ignore:
                    kept.append(ch)

                # check for end_id after keeping
                if end_id is not None and cid == end_id:
                    finished = True
                    break

            if kept:
                result.append(
                    {
                        **vol,
                        "chapters": kept,
                    }
                )

        return result

    @staticmethod
    def _resolve_img_path(
        img_dir: Path | None,
        url: str | None,
        *,
        name: str | None = None,
    ) -> Path | None:
        """
        Resolve the local path of an image if it exists.

        :param img_dir: The directory where images are stored.
        :param url: The source URL of the image.
        :param name: Optional explicit base name.
        :return: Path to the existing image, or None if not found or invalid.
        """
        if not img_dir or not url:
            return None

        path = img_dir / img_name(url, name=name)
        return path if path.is_file() else None

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        """
        Normalize a book identifier.

        Subclasses may override this method to transform the book ID
        into their preferred format.
        """
        return book_id.replace("/", "-")

    def _is_access_limited(self, html_list: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. login required, paywall, VIP, subscription, etc.)

        :param html_list: List of raw HTML strings.
        """
        return False

    def _skip_empty_chapter(self, html_list: list[str]) -> bool:
        """
        Return True if parse_chapter returns empty but should be skipped.
        """
        return False

    def _need_refetch(self, chap: ChapterDict) -> bool:
        """Override this hook to decide if a chapter needs refetch."""
        return False

    def _resolve_stage_selection(self, book_id: str) -> str:
        """
        Return the chosen stage name for export (e.g., 'raw', 'cleaner', 'corrector').
        Strategy:
          * If pipeline.json exists, walk pipeline in reverse and pick the last stage
            whose recorded sqlite file exists.
          * Fallback: any executed record with an existing sqlite file.
          * Else: 'raw'.
        """
        base_dir = self._raw_data_dir / book_id
        pipeline_path = base_dir / "pipeline.json"
        if not pipeline_path.is_file():
            return "raw"

        try:
            meta = json.loads(pipeline_path.read_text(encoding="utf-8"))
        except Exception:
            return "raw"

        pipeline: list[str] = meta.get("pipeline", [])
        if not pipeline:
            return "raw"

        for stg in reversed(pipeline):
            db_file = base_dir / f"chapter.{stg}.sqlite"
            info_file = base_dir / f"book_info.{stg}.json"
            if db_file.is_file() and info_file.is_file():
                return stg

        return "raw"

    def _render_txt_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _render_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _build_txt_header(self, book_info: BookInfoDict, name: str, author: str) -> str:
        """
        Top-of-file metadata block.
        """
        lines: list[str] = [name.strip()]

        if author:
            lines.append(f"作者：{author.strip()}")

        if serial_status := book_info.get("serial_status"):
            lines.append(f"状态：{serial_status.strip()}")

        if word_count := book_info.get("word_count"):
            lines.append(f"字数：{word_count.strip()}")

        if tags_list := book_info.get("tags"):
            tags = "、".join(t.strip() for t in tags_list if t)
            if tags:
                lines.append(f"标签：{tags}")

        if update_time := (book_info.get("update_time") or "").strip():
            lines.append(f"更新：{update_time}")

        if summary := (book_info.get("summary") or "").strip():
            lines.extend(["", summary])

        return "\n".join(lines).strip() + "\n\n"

    def _build_txt_volume_heading(self, vol_title: str, volume: VolumeInfoDict) -> str:
        """
        Render a volume heading. Include optional info if present.
        """
        meta_bits: list[str] = []

        if v_update_time := volume.get("update_time"):
            meta_bits.append(f"更新时间：{v_update_time}")

        if v_word_count := volume.get("word_count"):
            meta_bits.append(f"字数：{v_word_count}")

        if v_intro := (volume.get("volume_intro") or "").strip():
            meta_bits.append(f"简介：{v_intro}")

        line = f"=== {vol_title.strip()} ==="
        return f"{line}\n" + ("\n".join(meta_bits) + "\n\n" if meta_bits else "\n\n")

    def _build_txt_chapter(self, chap_title: str | None, chap: ChapterDict) -> str:
        """
        Render one chapter to text
        """
        # Title
        title_line = chap_title or chap.get("title", "").strip()

        cleaned = chap.get("content", "").strip()
        body = "\n".join(s for line in cleaned.splitlines() if (s := line.strip()))

        # Extras
        extras_txt = self._render_txt_extras(chap.get("extra", {}) or {})

        return (
            f"{title_line}\n\n{body}\n\n{extras_txt}\n\n"
            if extras_txt
            else f"{title_line}\n\n{body}\n\n"
        )

    def _build_epub_chapter(
        self,
        *,
        book: EpubBuilder,
        css: list[StyleSheet],
        cid: str,
        chap_title: str | None,
        chap: ChapterDict,
        img_dir: Path | None = None,
    ) -> Chapter:
        """
        Build a Chapter object with XHTML content and optionally place images
        from `chap.extra['image_positions']` (1-based index; 0 = before 1st paragraph).
        """
        title = chap_title or chap.get("title", "").strip()
        content = chap.get("content", "")

        extras = chap.get("extra") or {}
        image_positions = self._collect_img_map(extras)
        html_parts: list[str] = [f"<h2>{escape(title)}</h2>"]

        def _append_image(url: str) -> None:
            if not img_dir:
                return
            u = (url or "").strip()
            if not u:
                return
            if u.startswith("//"):
                u = "https:" + u
            if not (u.startswith("http://") or u.startswith("https://")):
                return
            try:
                local = self._resolve_img_path(img_dir, u)
                if not local:
                    return
                fname = book.add_image(local)
                img = f'<img src="../Images/{fname}" alt="image"/>'
                html_parts.append(self._IMAGE_WRAPPER.format(img=img))
            except Exception as e:
                self.logger.debug("EPUB image add failed for %s: %s", u, e)

        # Images before first paragraph
        for url in image_positions.get(0, []):
            _append_image(url)

        # Paragraphs + inline-after images
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            if ln := line.strip():
                html_parts.append(f"<p>{escape(ln)}</p>")
            for url in image_positions.get(i, []):
                _append_image(url)

        max_i = len(lines)
        for k, urls in image_positions.items():
            if k > max_i:
                for url in urls:
                    _append_image(url)

        if extras_epub := self._render_epub_extras(extras):
            html_parts.append(extras_epub)

        xhtml = "\n".join(html_parts)
        return Chapter(
            id=f"c_{cid}",
            filename=f"c{cid}.xhtml",
            title=title,
            content=xhtml,
            css=css,
        )

    @staticmethod
    def _collect_img_map(extras: dict[str, Any]) -> dict[int, list[str]]:
        """
        Collect and normalize `image_positions` into `{int: [str, ...]}`.
        """
        result: dict[int, list[str]] = {}
        raw_map = extras.get("image_positions")

        if not isinstance(raw_map, dict):
            return result
        for k, v in raw_map.items():
            try:
                key = int(k)
            except Exception:
                key = 0
            urls: list[str] = []
            if isinstance(v, list | tuple):
                for u in v:
                    if isinstance(u, str):
                        s = u.strip()
                        if s:
                            urls.append(s)
            elif isinstance(v, str):
                s = v.strip()
                if s:
                    urls.append(s)
            if urls:
                result.setdefault(key, []).extend(urls)
        return result

    @classmethod
    def _render_html_block(cls, text: str) -> str:
        """
        Wraps each non-empty (stripped) line with <p>.
        """
        return "\n".join(
            f"<p>{escape(s)}</p>" for ln in text.splitlines() if (s := ln.strip())
        )
