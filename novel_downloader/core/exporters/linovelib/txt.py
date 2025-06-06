#!/usr/bin/env python3
"""
novel_downloader.core.exporters.linovelib.txt
---------------------------------------------

Contains the logic for exporting novel content as a single `.txt` file.

This module defines `linovelib_export_as_txt` function, which assembles and formats
a novel based on metadata and chapter files found in the raw data directory.
It is intended to be used by `LinovelibExporter` as part of the save/export process.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from novel_downloader.utils.file_utils import save_as_txt
from novel_downloader.utils.text_utils import (
    format_chapter,
)

if TYPE_CHECKING:
    from .main_exporter import LinovelibExporter


def linovelib_export_as_txt(
    exporter: LinovelibExporter,
    book_id: str,
) -> None:
    """
    将 save_path 文件夹中该小说的所有章节 json 文件合并保存为一个完整的 txt 文件,
    并保存到 out_path 下

    处理流程：
      1. 从 book_info.json 中加载书籍信息 (包含书名、作者、简介及卷章节列表)
      2. 遍历各卷, 每个卷先追加卷标题, 然后依次追加该卷下各章节的标题和内容
      3. 将书籍元信息 (书名、作者、原文截至、内容简介) 与所有章节内容拼接
      4. 将最终结果保存到 out_path 下 (例如：`{book_name}.txt`)

    :param book_id: Identifier of the novel (used as subdirectory name).
    """
    TAG = "[exporter]"
    # --- Paths & options ---
    raw_base = exporter._raw_data_dir / book_id
    out_dir = exporter.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

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
    volumes = book_info.get("volumes", [])

    for vol in volumes:
        vol_name = vol.get("volume_name", "").strip()
        vol_intro = vol.get("volume_intro", "").strip()
        if vol_name:
            volume_header = f"\n\n{'=' * 6} {vol_name} {'=' * 6}\n\n"
            parts.append(volume_header)
            exporter.logger.info("%s Processing volume: %s", TAG, vol_name)
        if vol_intro:
            parts.append(f"{vol_intro}\n\n")
        for chap in vol.get("chapters", []):
            chap_id = chap.get("chapterId")
            chap_title = chap.get("title", "")
            if not chap_id:
                exporter.logger.warning("%s Missing chapterId, skipping: %s", TAG, chap)
                continue

            chapter_data = exporter._get_chapter(book_id, chap_id)
            if not chapter_data:
                exporter.logger.info(
                    "%s Missing chapter file in: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            # Extract structured fields
            title = chapter_data.get("title", chap_title).strip()
            content = chapter_data.get("content", "").strip()

            parts.append(format_chapter(title, content, ""))

    # --- Build header ---
    name = book_info.get("book_name")
    author = book_info.get("author")
    words = book_info.get("word_count")
    updated = book_info.get("update_time")
    summary = book_info.get("summary")

    fields = [
        ("书名", name),
        ("作者", author),
        ("总字数", words),
        ("更新日期", updated),
    ]
    header_lines = [f"{label}: {value}" for label, value in fields if value]

    if summary:
        header_lines.append("内容简介:")
        header_lines.append(summary)

    header_lines += ["", "-" * 10, ""]

    header = "\n".join(header_lines)

    final_text = header + "\n\n" + "\n\n".join(parts).strip()

    # --- Determine output file path ---
    out_name = exporter.get_filename(title=name, author=author, ext="txt")
    out_path = out_dir / out_name

    # --- Save final text ---
    try:
        save_as_txt(content=final_text, filepath=out_path)
        exporter.logger.info("%s Novel saved to: %s", TAG, out_path)
    except Exception as e:
        exporter.logger.error("%s Failed to save file: %s", TAG, e)
    return
