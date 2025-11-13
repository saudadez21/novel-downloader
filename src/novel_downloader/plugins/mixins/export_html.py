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
from novel_downloader.libs.html_builder import HtmlBuilder, HtmlChapter, HtmlVolume
from novel_downloader.schemas import BookConfig, ChapterDict, ExporterConfig

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
            img_dir: Path | None = None,
        ) -> HtmlChapter:
            ...

        def _xp_html_extras(self, extras: dict[str, Any]) -> str:
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

        img_dir = raw_base / "medias"

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

                    chapter_obj = self._xp_html_chapter(
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
            logger.info(
                "Exported HTML (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            logger.error(
                "Failed to write HTML (site=%s, book=%s): %s",
                self._site,
                book_id,
                e,
            )
            return []
        return [out_path]

    def _xp_html_chapter(
        self: "ExportHtmlClientContext",
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
        image_positions = self._build_image_map(chap)
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

                    local = self._resolve_image_path(img_dir, data)
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
                html_parts.append(
                    f'<img src="../media/{fname}" alt="image" class="chapter-image"/>'
                )

            except Exception as e:
                logger.debug("EPUB image add failed: %s", e)

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

        if extras_part := self._xp_html_extras(extras):
            html_parts.append(extras_part)

        html_str = "\n".join(html_parts)
        return HtmlChapter(
            filename=f"c{cid}.html",
            title=title,
            content=html_str,
        )

    def _xp_html_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""
