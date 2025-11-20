#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins.export_html
-------------------------------------------
"""

import base64
import logging
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.filesystem import (
    font_filename,
    format_filename,
    image_filename,
)
from novel_downloader.libs.html_builder import HtmlBuilder, HtmlChapter, HtmlVolume
from novel_downloader.schemas import (
    BookConfig,
    ChapterDict,
    ExporterConfig,
    MediaResource,
)

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from novel_downloader.plugins.protocols import _ClientContext

    class ExportHtmlClientContext(_ClientContext, Protocol):
        """"""

        def _xp_html_chapter(
            self,
            *,
            builder: HtmlBuilder,
            cid: str,
            chap_title: str | None,
            chap: ChapterDict,
            media_dir: Path | None = None,
        ) -> HtmlChapter:
            ...

        def _xp_html_extras(self, extras: dict[str, Any]) -> str:
            ...

        def _xp_html_chap_post(
            self, html_parts: list[str], chap: ChapterDict
        ) -> list[str]:
            ...


class ExportHtmlMixin:
    """"""

    def _export_book_html(
        self: "ExportHtmlClientContext",
        book: BookConfig,
        cfg: ExporterConfig,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """
        Export a novel as HTML files.
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
        cover_path = self._resolve_image_path(
            media_dir, book_info.get("cover_url"), name="cover"
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

                    chapter_obj = self._xp_html_chapter(
                        builder=builder,
                        cid=cid,
                        chap_title=ch_title,
                        chap=ch,
                        media_dir=media_dir,
                    )

                    curr_vol.chapters.append(chapter_obj)

                if curr_vol.chapters:
                    builder.add_volume(curr_vol)

        out_name = format_filename(
            cfg.filename_template,
            title=name,
            author=author,
            append_timestamp=cfg.append_timestamp,
        )
        out_path = builder.export(self._output_dir, folder=out_name)
        logger.info(
            "Exported HTML (site=%s, book=%s): %s", self._site, book_id, out_path
        )
        return [out_path]

    def _xp_html_chapter(
        self: "ExportHtmlClientContext",
        *,
        builder: HtmlBuilder,
        cid: str,
        chap_title: str | None,
        chap: ChapterDict,
        media_dir: Path,
    ) -> HtmlChapter:
        """
        Build a Chapter object with HTML content and optionally place images / font.
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
                    if url.startswith("//"):
                        url = "https:" + url
                    if url.startswith(("http://", "https://")):
                        local = media_dir / image_filename(url)
                        if local and local.is_file():
                            fname = builder.add_image(local)

                elif b64 := res.get("base64"):
                    mime = res.get("mime", "image/png")
                    raw = base64.b64decode(b64)
                    fname = builder.add_image_bytes(raw, mime_type=mime)

                if fname:
                    alt = escape(res.get("alt") or "image")
                    html_parts.append(
                        f'<img src="../media/{fname}" alt="{alt}" class="chapter-image"/>'  # noqa: E501
                    )

            except Exception as e:
                logger.debug("HTML image add failed: %s", e)

        for r in resources:
            typ = r.get("type")

            if typ == "font":
                try:
                    if url := r.get("url"):
                        local = media_dir / font_filename(url)
                        if local.is_file() and (f := builder.add_font(local)):
                            added_fonts.append(f)

                    elif b64 := r.get("base64"):
                        raw = base64.b64decode(b64)
                        if f := builder.add_font_bytes(raw):
                            added_fonts.append(f)

                except Exception as e:
                    logger.debug("EPUB font add failed: %s", e)

            elif typ == "image":
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

        html_parts = self._xp_html_chap_post(html_parts, chap)
        html_str = "\n".join(html_parts)
        extras_part = self._xp_html_extras(chap.get("extra") or {})

        return HtmlChapter(
            filename=f"c{cid}.html",
            title=title,
            content=html_str,
            extra_content=extras_part,
            fonts=added_fonts,
        )

    def _xp_html_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _xp_html_chap_post(self, html_parts: list[str], chap: ChapterDict) -> list[str]:
        """Allows subclasses to inject HTML or modify structure."""
        return html_parts
