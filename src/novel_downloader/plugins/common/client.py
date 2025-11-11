#!/usr/bin/env python3
"""
novel_downloader.plugins.common.client
--------------------------------------
"""

import asyncio
import base64
from html import escape
from pathlib import Path
from typing import Any, Final, final

from novel_downloader.infra.paths import EPUB_CSS_MAIN_PATH
from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.epub_builder import (
    EpubBuilder,
    EpubChapter,
    EpubStyleSheet,
    EpubVolume,
)
from novel_downloader.libs.filesystem import sanitize_filename, write_file
from novel_downloader.libs.html_builder import HtmlBuilder, HtmlChapter, HtmlVolume
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.client import BaseClient
from novel_downloader.plugins.protocols import (
    DownloadUI,
    LoginUI,
    ProcessUI,
)
from novel_downloader.plugins.utils.stage_runner import StageRunner
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ExporterConfig,
    ProcessorConfig,
    VolumeInfoDict,
)


@final
class StopToken:
    """Typed sentinel used to end queues."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "STOP"


STOP: Final[StopToken] = StopToken()


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
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        if ui:
            await ui.on_start(book)

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
        raw_base = self._raw_data_dir / book.book_id

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

            self.logger.info(
                "All stages completed successfully for book %s", book.book_id
            )

        except Exception as e:
            self.logger.warning(
                "Processing failed at stage '%s' for book %s: %s",
                stage_name,
                book.book_id,
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
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

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

                imgs = self._extract_img_urls(chap)
                await self.fetcher.download_images(
                    img_dir,
                    imgs,
                    batch_size=concurrent,
                    on_exist="overwrite" if force_update else "skip",
                )

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
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            return []

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

    def export_as_html(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """
        Export a novel as HTML files.
        """
        cfg = cfg or ExporterConfig()
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            return []

        img_dir = raw_base / "images"

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
        cover_path = self._resolve_img_path(
            img_dir, book_info.get("cover_url"), name="cover"
        )
        cover = cover_path.read_bytes() if cover_path else None

        # --- Initialize EPUB ---
        builder = HtmlBuilder(
            title=name,
            author=author,
            description=book_info.get("summary", ""),
            cover=cover,
            subject=book_info.get("tags", []),
            serial_status=book_info.get("serial_status", ""),
            word_count=book_info.get("word_count", ""),
        )

        # --- Compile columes ---
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, vol in enumerate(vols, start=1):
                vol_title = vol.get("volume_name") or f"卷 {v_idx}"

                curr_vol = HtmlVolume(
                    title=vol_title,
                    intro=vol.get("volume_intro", ""),
                )

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
                for ch_info in vol.get("chapters", []):
                    cid = ch_info.get("chapterId")
                    ch_title = ch_info.get("title")
                    if not cid:
                        continue

                    ch = chap_map.get(cid)
                    if not ch:
                        continue

                    chapter_obj = self._build_html_chapter(
                        builder=builder,
                        cid=cid,
                        chap_title=ch_title,
                        chap=ch,
                        img_dir=img_dir,
                    )

                    curr_vol.chapters.append(chapter_obj)

                if curr_vol.chapters:
                    builder.add_volume(curr_vol)

        try:
            out_path = builder.export(self._output_dir)
            self.logger.info(
                "Exported HTML (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            self.logger.error(
                "Failed to write HTML (site=%s, book=%s): %s",
                self._site,
                book_id,
                e,
            )
            return []
        return [out_path]

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
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            return []

        img_dir: Path | None = None
        if cfg.include_picture:
            img_dir = raw_base / "images"

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

        css_text = EPUB_CSS_MAIN_PATH.read_text(encoding="utf-8")
        main_css = EpubStyleSheet(
            id="main_style", content=css_text, filename="main.css"
        )

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
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            return []

        img_dir: Path | None = None
        if cfg.include_picture:
            img_dir = raw_base / "images"

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
        css_text = EPUB_CSS_MAIN_PATH.read_text(encoding="utf-8")
        main_css = EpubStyleSheet(
            id="main_style", content=css_text, filename="main.css"
        )
        epub.add_stylesheet(main_css)

        # --- Compile columes ---
        seen_cids: set[str] = set()
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, vol in enumerate(vols, start=1):
                vol_title = vol.get("volume_name") or f"卷 {v_idx}"

                vol_cover = self._resolve_img_path(img_dir, vol.get("volume_cover"))

                curr_vol = EpubVolume(
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

                imgs = self._extract_img_urls(chap)
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

    def _render_txt_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _build_epub_chapter(
        self,
        *,
        book: EpubBuilder,
        css: list[EpubStyleSheet],
        cid: str,
        chap_title: str | None,
        chap: ChapterDict,
        img_dir: Path | None = None,
    ) -> EpubChapter:
        """
        Build a Chapter object with XHTML content and optionally place images
        from `chap.extra['image_positions']` (1-based index; 0 = before 1st paragraph).
        """
        title = chap_title or chap.get("title", "").strip()
        content = chap.get("content", "")

        extras = chap.get("extra") or {}
        image_positions = self._collect_img_map(chap)
        html_parts: list[str] = [f"<h2>{escape(title)}</h2>"]

        def _append_image(item: dict[str, Any]) -> None:
            if not img_dir:
                return

            typ = item.get("type")
            data = (item.get("data") or "").strip()
            if not data:
                return

            try:
                if typ == "url":
                    # ---- Handle normal URL ----
                    if data.startswith("//"):
                        data = "https:" + data
                    if not (data.startswith("http://") or data.startswith("https://")):
                        return

                    local = self._resolve_img_path(img_dir, data)
                    if not local:
                        return

                    fname = book.add_image(local)

                elif typ == "base64":
                    # ---- Handle base64-encoded image ----
                    mime = item.get("mime", "image/png")
                    raw = base64.b64decode(data)
                    fname = book.add_image_bytes(raw, mime_type=mime)

                else:
                    # Unknown type
                    return

                # ---- Append <img> HTML ----
                img_tag = f'<img src="../Images/{fname}" alt="image"/>'
                html_parts.append(self._IMAGE_WRAPPER.format(img=img_tag))

            except Exception as e:
                self.logger.debug("EPUB image add failed: %s", e)

        # Images before first paragraph
        for item in image_positions.get(0, []):
            _append_image(item)

        # Paragraphs + inline-after images
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            if ln := line.strip():
                html_parts.append(f"<p>{escape(ln)}</p>")
            for item in image_positions.get(i, []):
                _append_image(item)

        max_i = len(lines)
        for k, items in image_positions.items():
            if k > max_i:
                for item in items:
                    _append_image(item)

        if extras_epub := self._render_epub_extras(extras):
            html_parts.append(extras_epub)

        xhtml = "\n".join(html_parts)
        return EpubChapter(
            id=f"c_{cid}",
            filename=f"c{cid}.xhtml",
            title=title,
            content=xhtml,
            css=css,
        )

    def _render_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _build_html_chapter(
        self,
        *,
        builder: HtmlBuilder,
        cid: str,
        chap_title: str | None,
        chap: ChapterDict,
        img_dir: Path | None = None,
    ) -> HtmlChapter:
        """
        Build a Chapter object with HTML content and optionally place images
        from `chap.extra['image_positions']` (1-based index; 0 = before 1st paragraph).
        """
        title = chap_title or chap.get("title", "").strip()
        content = chap.get("content", "")

        extras = chap.get("extra") or {}
        image_positions = self._collect_img_map(chap)
        html_parts: list[str] = []

        def _append_image(item: dict[str, Any]) -> None:
            if not img_dir:
                return

            typ = item.get("type")
            data = (item.get("data") or "").strip()
            if not data:
                return

            try:
                if typ == "url":
                    # ---- Handle normal URL ----
                    if data.startswith("//"):
                        data = "https:" + data
                    if not (data.startswith("http://") or data.startswith("https://")):
                        return

                    local = self._resolve_img_path(img_dir, data)
                    if not local:
                        return

                    fname = builder.add_image(local)

                elif typ == "base64":
                    # ---- Handle base64-encoded image ----
                    mime = item.get("mime", "image/png")
                    raw = base64.b64decode(data)
                    fname = builder.add_image_bytes(raw, mime_type=mime)

                else:
                    # Unknown type
                    return

                # ---- Append <img> HTML ----
                img_tag = (
                    f'<img src="../media/{fname}" alt="image" class="chapter-image"/>'
                )
                html_parts.append(self._IMAGE_WRAPPER.format(img=img_tag))

            except Exception as e:
                self.logger.debug("EPUB image add failed: %s", e)

        # Images before first paragraph
        for item in image_positions.get(0, []):
            _append_image(item)

        # Paragraphs + inline-after images
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            if ln := line.strip():
                html_parts.append(f"<p>{escape(ln)}</p>")
            for item in image_positions.get(i, []):
                _append_image(item)

        max_i = len(lines)
        for k, items in image_positions.items():
            if k > max_i:
                for item in items:
                    _append_image(item)

        if extras_part := self._render_html_extras(extras):
            html_parts.append(extras_part)

        html_str = "\n".join(html_parts)
        return HtmlChapter(
            filename=f"c{cid}.html",
            title=title,
            content=html_str,
        )

    def _render_html_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""
