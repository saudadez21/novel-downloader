#!/usr/bin/env python3
"""
novel_downloader.core.exporters.linovelib.txt
---------------------------------------------

Defines `linovelib_export_as_txt` to assemble and export a Linovelib novel
into a single `.txt` file. Intended for use by `LinovelibExporter`.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from novel_downloader.core.exporters.txt_util import (
    build_txt_chapter,
    build_txt_header,
)
from novel_downloader.utils import get_cleaner, save_as_txt

if TYPE_CHECKING:
    from .main_exporter import LinovelibExporter


def linovelib_export_as_txt(
    exporter: LinovelibExporter,
    book_id: str,
) -> None:
    """
    Merge all chapter JSON files under `raw_data/<book_id>` into one TXT,
    then write it to the exporter's output directory.

    Steps:
      1. Read metadata from `book_info.json`.
      2. For each volume:
         - Clean & append the volume title.
         - Clean & append optional volume intro.
         - For each chapter: load JSON, clean title & content, then append.
      3. Build a header block with metadata.
      4. Concatenate header + all chapter blocks, then save as `{book_name}.txt`.

    :param exporter: The LinovelibExporter instance.
    :param book_id: Identifier of the novel (subdirectory under raw data).
    """
    TAG = "[exporter]"
    # --- Paths & options ---
    raw_base = exporter._raw_data_dir / book_id
    out_dir = exporter.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    cleaner = get_cleaner(
        enabled=exporter._config.clean_text,
        config=exporter._config.cleaner_cfg,
    )

    # --- Load book_info.json ---
    info_path = raw_base / "book_info.json"
    try:
        info_text = info_path.read_text(encoding="utf-8")
        book_info = json.loads(info_text)
    except Exception as e:
        exporter.logger.error("%s Failed to load %s: %s", TAG, info_path, e)
        return

    # --- Compile chapters ---
    parts: list[str] = []

    for vol in book_info.get("volumes", []):
        vol_title = cleaner.clean_title(vol.get("volume_name", ""))
        if vol_title:
            parts.append(f"\n\n{'=' * 6} {vol_title} {'=' * 6}\n\n")
            exporter.logger.info("%s Processing volume: %s", TAG, vol_title)

        vol_intro = cleaner.clean_content(vol.get("volume_intro", ""))
        if vol_intro:
            parts.append(f"{vol_intro}\n\n")

        for chap in vol.get("chapters", []):
            chap_id = chap.get("chapterId")
            if not chap_id:
                exporter.logger.warning("%s Missing chapterId, skipping: %s", TAG, chap)
                continue

            chap_title = cleaner.clean_title(chap.get("title", ""))

            data = exporter._get_chapter(book_id, chap_id)
            if not data:
                exporter.logger.info(
                    "%s Missing chapter file in: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            # Extract structured fields
            title = cleaner.clean_title(data.get("title", chap_title))
            content = cleaner.clean_content(data.get("content", ""))

            parts.append(build_txt_chapter(title=title, paragraphs=content, extras={}))

    # --- Build header ---
    name = book_info.get("book_name")
    author = book_info.get("author")
    words = book_info.get("word_count")
    updated = book_info.get("update_time")
    summary = book_info.get("summary")

    header_fields = [
        ("书名", name),
        ("作者", author),
        ("总字数", words),
        ("更新日期", updated),
        ("内容简介", summary),
    ]

    header = build_txt_header(header_fields)

    final_text = header + "\n\n" + "\n\n".join(parts).strip()

    # --- Determine output file path ---
    out_name = exporter.get_filename(title=name, author=author, ext="txt")
    out_path = out_dir / out_name

    # --- Save final text ---
    result = save_as_txt(content=final_text, filepath=out_path)
    if result:
        exporter.logger.info("%s Novel saved to: %s", TAG, out_path)
    else:
        exporter.logger.error("%s Failed to write novel to %s", TAG, out_path)
    return
