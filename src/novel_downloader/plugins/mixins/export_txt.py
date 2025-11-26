#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins.export_txt
------------------------------------------
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.filesystem import (
    format_filename,
    sanitize_filename,
    write_file,
)
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ExporterConfig,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from novel_downloader.plugins.protocols import _ClientContext

    class ExportTxtClientContext(_ClientContext, Protocol):
        """"""

        def _xp_txt_header(
            self, book_info: BookInfoDict, name: str, author: str
        ) -> str: ...

        def _xp_txt_volume_heading(
            self, vol_title: str, volume: VolumeInfoDict
        ) -> str: ...

        def _xp_txt_chapter(self, chap_title: str | None, chap: ChapterDict) -> str: ...

        def _xp_txt_missing_chapter(
            self,
            *,
            cid: str,
            chap_title: str | None,
        ) -> str: ...

        def _xp_txt_extras(self, extras: dict[str, Any]) -> str: ...


class ExportTxtMixin:
    """"""

    def _export_book_txt(
        self: "ExportTxtClientContext",
        book: BookConfig,
        cfg: ExporterConfig,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> list[Path]:
        """
        Export a novel as a single text file by merging all chapter data.
        """
        book_id = book.book_id
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = book.ignore_ids

        # --- Load book data ---
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            return []

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
        header_txt = self._xp_txt_header(book_info, name, author)

        # --- Build body by volumes & chapters ---
        parts: list[str] = [header_txt]
        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            for v_idx, volume in enumerate(vols, start=1):
                vol_title = volume.get("volume_name") or f"卷 {v_idx}"
                parts.append(self._xp_txt_volume_heading(vol_title, volume))

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
                        if cfg.render_missing_chapter:
                            parts.append(
                                self._xp_txt_missing_chapter(
                                    cid=cid,
                                    chap_title=ch_title,
                                )
                            )
                        continue

                    parts.append(self._xp_txt_chapter(ch_title, ch))

        final_text = "\n".join(parts)

        # --- Determine output file path ---
        out_name = format_filename(
            cfg.filename_template,
            title=name,
            author=author,
            append_timestamp=cfg.append_timestamp,
            ext="txt",
        )
        out_path = self._output_dir / sanitize_filename(out_name)

        # --- Save final text ---
        result = write_file(content=final_text, filepath=out_path, on_exist="overwrite")
        logger.info(
            "Exported TXT (site=%s, book=%s): %s", self._site, book_id, out_path
        )
        return [result]

    def _export_chapter_txt(
        self: "ExportTxtClientContext",
        book_id: str,
        chapter_id: str,
        cfg: ExporterConfig,
        *,
        stage: str | None = None,
        **kwargs: Any,
    ) -> Path | None:
        """Export a single chapter into a TXT file."""
        raw_base = self._raw_data_dir / book_id
        if not raw_base.is_dir():
            return None

        # --- stage ---
        stage = stage or self._detect_latest_stage(book_id)

        # --- Load chapter ---
        dbfile = raw_base / f"chapter.{stage}.sqlite"
        if not dbfile.exists():
            return None

        with ChapterStorage(raw_base, filename=f"chapter.{stage}.sqlite") as storage:
            chap = storage.get_chapter(chapter_id)

        if chap is None:
            return None

        chap_title = (chap.get("title") or f"chapter_{chapter_id}").strip()
        final_text = self._xp_txt_chapter(chap_title, chap)

        # --- Output file name ---
        out_name = format_filename(
            cfg.filename_template,
            title=chap_title,
            author="Unknown",
            append_timestamp=cfg.append_timestamp,
            ext="txt",
        )
        out_path = self._output_dir / sanitize_filename(out_name)

        # --- Save file ---
        result = write_file(
            content=final_text,
            filepath=out_path,
            on_exist="overwrite",
        )

        logger.info(
            "Exported TXT chapter (site=%s, book=%s, chapter=%s): %s",
            self._site,
            book_id,
            chapter_id,
            out_path,
        )
        return result

    def _xp_txt_header(self, book_info: BookInfoDict, name: str, author: str) -> str:
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

    def _xp_txt_volume_heading(self, vol_title: str, volume: VolumeInfoDict) -> str:
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

    def _xp_txt_chapter(self, chap_title: str | None, chap: ChapterDict) -> str:
        """
        Render one chapter to text
        """
        # Title
        title_line = chap_title or chap.get("title", "").strip()

        cleaned = chap.get("content", "").strip()
        body = "\n".join(s for line in cleaned.splitlines() if (s := line.strip()))

        # Extras
        extras_txt = self._xp_txt_extras(chap.get("extra", {}) or {})

        return (
            f"{title_line}\n\n{body}\n\n{extras_txt}\n\n"
            if extras_txt
            else f"{title_line}\n\n{body}\n\n"
        )

    def _xp_txt_missing_chapter(
        self,
        *,
        cid: str,
        chap_title: str | None,
    ) -> str:
        """
        Render a placeholder text block for missing or inaccessible chapters.
        """
        title = chap_title or f"Chapter {cid}"
        return f"{title}\n\n本章内容暂不可用\n\n"

    def _xp_txt_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""
