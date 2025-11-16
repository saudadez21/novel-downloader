#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins.export_epub
-------------------------------------------
"""

import base64
import logging
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.epub_builder import EpubBuilder, EpubChapter, EpubVolume
from novel_downloader.libs.filesystem import (
    font_filename,
    format_filename,
    image_filename,
    sanitize_filename,
)
from novel_downloader.schemas import (
    BookConfig,
    ChapterDict,
    ExporterConfig,
    MediaResource,
)

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from novel_downloader.plugins.protocols import _ClientContext

    class ExportEpubClientContext(_ClientContext, Protocol):
        """"""

        _IMAGE_WRAPPER: str

        def _xp_epub_chapter(
            self,
            *,
            book: EpubBuilder,
            cid: str,
            chap_title: str | None,
            chap: ChapterDict,
            media_dir: Path,
            include_picture: bool = True,
        ) -> EpubChapter:
            ...

        def _xp_epub_extras(self, extras: dict[str, Any]) -> str:
            ...

        def _xp_epub_chap_post(
            self, html_parts: list[str], chap: ChapterDict
        ) -> list[str]:
            ...


class ExportEpubMixin:
    """"""

    _IMAGE_WRAPPER = '<div class="duokan-image-single illus">{img}</div>'

    def _export_volume_epub(
        self: "ExportEpubClientContext",
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

        media_dir = raw_base / "media"

        stage = stage or self._detect_latest_stage(book_id)
        book_info = self._load_book_info(book_id, stage=stage)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return []

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""
        book_summary = book_info.get("summary", "")

        # --- Generate intro + cover ---
        cover_path = self._resolve_image_path(media_dir, book_info.get("cover_url"))

        # --- Compile columes ---
        outputs: list[Path] = []
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, vol in enumerate(vols, start=1):
                vol_title = vol.get("volume_name") or f"卷 {v_idx}"

                vol_cover = self._resolve_image_path(media_dir, vol.get("volume_cover"))
                vol_cover = vol_cover or cover_path

                builder = EpubBuilder(
                    title=f"{name} - {vol_title}",
                    author=author,
                    description=vol.get("volume_intro") or book_summary,
                    cover_path=vol_cover,
                    subject=book_info.get("tags", []),
                    serial_status=book_info.get("serial_status", ""),
                    word_count=vol.get("word_count", ""),
                    uid=f"{self._site}_{book_id}_v{v_idx}",
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
                seen_cids: set[str] = set()
                for ch_info in vol.get("chapters", []):
                    cid = ch_info.get("chapterId")
                    ch_title = ch_info.get("title")
                    if not cid or cid in seen_cids:
                        continue

                    ch = chap_map.get(cid)
                    if not ch:
                        continue

                    chapter_obj = self._xp_epub_chapter(
                        book=builder,
                        cid=cid,
                        chap_title=ch_title,
                        chap=ch,
                        media_dir=media_dir,
                        include_picture=cfg.include_picture,
                    )
                    builder.add_chapter(chapter_obj)
                    seen_cids.add(cid)

                out_name = format_filename(
                    cfg.filename_template,
                    title=vol_title,
                    author=author,
                    append_timestamp=cfg.append_timestamp,
                    ext="epub",
                )
                out_path = self._output_dir / sanitize_filename(out_name)

                try:
                    outputs.append(builder.export(out_path))
                    logger.info(
                        "Exported EPUB (site=%s, book=%s): %s",
                        self._site,
                        book_id,
                        out_path,
                    )
                except Exception as e:
                    logger.error(
                        "Failed to write EPUB (site=%s, book=%s) to %s: %s",
                        self._site,
                        book_id,
                        out_path,
                        e,
                    )
        return outputs

    def _export_book_epub(
        self: "ExportEpubClientContext",
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

        media_dir = raw_base / "media"

        stage = stage or self._detect_latest_stage(book_id)
        book_info = self._load_book_info(book_id, stage=stage)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return []

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""

        # --- Generate intro + cover ---
        cover_path = self._resolve_image_path(
            media_dir, book_info.get("cover_url"), name="cover"
        )

        # --- Initialize EPUB ---
        builder = EpubBuilder(
            title=name,
            author=author,
            description=book_info.get("summary", ""),
            cover_path=cover_path,
            subject=book_info.get("tags", []),
            serial_status=book_info.get("serial_status", ""),
            word_count=book_info.get("word_count", ""),
            uid=f"{self._site}_{book_id}",
        )

        # --- Compile columes ---
        seen_cids: set[str] = set()
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, vol in enumerate(vols, start=1):
                vol_title = vol.get("volume_name") or f"卷 {v_idx}"

                vol_cover = self._resolve_image_path(media_dir, vol.get("volume_cover"))

                curr_vol = EpubVolume(
                    id=f"vol_{v_idx}",
                    title=vol_title,
                    intro=vol.get("volume_intro", ""),
                    cover_path=vol_cover,
                )

                # Collect chapter ids then batch fetch
                cids = [
                    c["chapterId"]
                    for c in vol.get("chapters", [])
                    if c.get("chapterId")
                ]
                if not cids:
                    builder.add_volume(curr_vol)
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

                    chapter_obj = self._xp_epub_chapter(
                        book=builder,
                        cid=cid,
                        chap_title=ch_title,
                        chap=ch,
                        media_dir=media_dir,
                        include_picture=cfg.include_picture,
                    )

                    curr_vol.chapters.append(chapter_obj)
                    seen_cids.add(cid)

                if curr_vol.chapters:
                    builder.add_volume(curr_vol)

        # --- Finalize EPUB ---
        out_name = format_filename(
            cfg.filename_template,
            title=name,
            author=author,
            append_timestamp=cfg.append_timestamp,
            ext="epub",
        )
        out_path = self._output_dir / sanitize_filename(out_name)

        try:
            builder.export(out_path)
            logger.info(
                "Exported EPUB (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            logger.error(
                "Failed to write EPUB (site=%s, book=%s) to %s: %s",
                self._site,
                book_id,
                out_path,
                e,
            )
            return []
        return [out_path]

    def _xp_epub_chapter(
        self: "ExportEpubClientContext",
        *,
        book: EpubBuilder,
        cid: str,
        chap_title: str | None,
        chap: ChapterDict,
        media_dir: Path,
        include_picture: bool = True,
    ) -> EpubChapter:
        """
        Build a Chapter object with XHTML content and optionally place images / font.
        """
        title = chap_title or chap.get("title", "").strip()
        content = chap.get("content", "")
        resources: list[MediaResource] = chap.get("extra", {}).get("resources", [])

        lines = content.splitlines()
        max_i = len(lines)

        images_by_index: dict[int, list[MediaResource]] = {}
        added_fonts = []
        html_parts: list[str] = []

        def _append_image(res: MediaResource) -> None:
            fname: str | None = None
            try:
                if url := res.get("url"):
                    local = media_dir / image_filename(url)
                    if local and local.is_file():
                        fname = book.add_image(local)

                elif b64 := res.get("base64"):
                    mime = res.get("mime", "image/png")
                    raw = base64.b64decode(b64)
                    fname = book.add_image_bytes(raw, mime_type=mime)

                if fname:
                    alt = escape(res.get("alt") or "image")
                    tag = f'<img src="../Images/{fname}" alt="{alt}"/>'
                    html_parts.append(self._IMAGE_WRAPPER.format(img=tag))

            except Exception as e:
                logger.debug("EPUB image add failed: %s", e)

        for r in resources:
            typ = r.get("type")

            if typ == "font":
                try:
                    if url := r.get("url"):
                        local = media_dir / font_filename(url)
                        if local.is_file() and (f := book.add_font(local)):
                            added_fonts.append(f)

                    elif b64 := r.get("base64"):
                        raw = base64.b64decode(b64)
                        if f := book.add_font_bytes(raw):
                            added_fonts.append(f)

                except Exception as e:
                    logger.debug("EPUB font add failed: %s", e)

            elif typ == "image" and include_picture:
                idx = r.get("paragraph_index", max_i)
                if idx == 0:
                    _append_image(r)
                    continue

                idx = min(idx, max_i)
                images_by_index.setdefault(idx, []).append(r)

        for i, ln in enumerate(lines, start=1):
            if ln := ln.strip():
                html_parts.append(f"<p>{escape(ln)}</p>")

            if items := images_by_index.get(i):
                for res in items:
                    _append_image(res)

        html_parts = self._xp_epub_chap_post(html_parts, chap)
        xhtml_str = "\n".join(html_parts)
        extra_content = self._xp_epub_extras(chap.get("extra") or {})

        return EpubChapter(
            id=f"c_{cid}",
            filename=f"c{cid}.xhtml",
            title=title,
            fonts=added_fonts,
            content=xhtml_str,
            extra_content=extra_content,
        )

    def _xp_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _xp_epub_chap_post(self, html_parts: list[str], chap: ChapterDict) -> list[str]:
        """Allows subclasses to inject HTML or modify structure."""
        return html_parts
