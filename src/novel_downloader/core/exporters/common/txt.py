#!/usr/bin/env python3
"""
novel_downloader.core.exporters.common.txt
------------------------------------------

Defines `common_export_as_txt` to assemble and export a novel
into a single `.txt` file. Intended for use by `CommonExporter`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from novel_downloader.core.exporters.txt_util import (
    build_txt_chapter,
    build_txt_header,
)
from novel_downloader.utils import get_cleaner, write_file

if TYPE_CHECKING:
    from .main_exporter import CommonExporter


def common_export_as_txt(
    exporter: CommonExporter,
    book_id: str,
) -> Path | None:
    """
    Export a novel as a single text file by merging all chapter data.

    Steps:
      1. Load book metadata.
      2. For each volume:
         a. Append the volume title.
         b. Batch-fetch all chapters in that volume to minimize SQLite calls.
         c. Append each chapter's title, content, and optional author note.
      3. Build a header with book metadata and the latest chapter title.
      4. Concatenate header and all chapter contents.
      5. Save the resulting .txt file to the output directory
         (e.g., '{book_name}.txt').

    :param exporter: The CommonExporter instance managing paths and config.
    :param book_id: Identifier of the novel (subdirectory under raw data).
    """
    TAG = "[Exporter]"
    # --- Paths & options ---
    out_dir = exporter.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cleaner = get_cleaner(
        enabled=exporter._config.clean_text,
        config=exporter._config.cleaner_cfg,
    )

    # --- Load book_info.json ---
    book_info = exporter._load_book_info(book_id)
    if not book_info:
        return None

    # --- Compile chapters ---
    parts: list[str] = []
    latest_chapter_title: str = ""

    for vol in book_info.get("volumes", []):
        vol_name = cleaner.clean_title(vol.get("volume_name", ""))
        if vol_name:
            # e.g. "\n\n====== 第三卷 ======\n\n"
            parts.append(f"\n\n{'=' * 6} {vol_name} {'=' * 6}\n\n")
            exporter.logger.info("%s Processing volume: %s", TAG, vol_name)

        # Batch-fetch chapters for this volume
        chap_ids = [
            chap["chapterId"]
            for chap in vol.get("chapters", [])
            if chap.get("chapterId")
        ]
        chap_map = exporter._get_chapters(book_id, chap_ids)

        for chap_meta in vol.get("chapters", []):
            chap_id = chap_meta.get("chapterId")
            if not chap_id:
                exporter.logger.warning(
                    "%s Missing chapterId, skipping: %s", TAG, chap_meta
                )
                continue

            chap_title = chap_meta.get("title", "")
            data = chap_map.get(chap_id)
            if not data:
                exporter.logger.info(
                    "%s Missing chapter: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            # Extract and clean fields
            title = cleaner.clean_title(data.get("title", chap_title))
            content = cleaner.clean_content(data.get("content", ""))
            extra = data.get("extra", {})
            author_note = cleaner.clean_content(extra.get("author_say", ""))

            extras = {"作者说": author_note} if author_note else {}
            parts.append(
                build_txt_chapter(title=title, paragraphs=content, extras=extras)
            )

            latest_chapter_title = title

    # --- Build header ---
    name = book_info.get("book_name") or ""
    author = book_info.get("author") or ""
    words = book_info.get("word_count") or ""
    updated = book_info.get("update_time") or ""
    summary = book_info.get("summary") or ""

    header_fields = [
        ("书名", name),
        ("作者", author),
        ("总字数", words),
        ("更新日期", updated),
        ("原文截至", latest_chapter_title),
        ("内容简介", summary),
    ]

    header = build_txt_header(header_fields)

    final_text = header + "\n\n" + "\n\n".join(parts).strip()

    # --- Determine output file path ---
    out_name = exporter.get_filename(title=name, author=author, ext="txt")
    out_path = out_dir / out_name

    # --- Save final text ---
    result = write_file(
        content=final_text,
        filepath=out_path,
        write_mode="w",
        on_exist="overwrite",
    )
    if result:
        exporter.logger.info("%s Novel saved to: %s", TAG, out_path)
    else:
        exporter.logger.error("%s Failed to write novel to %s", TAG, out_path)
    return result
