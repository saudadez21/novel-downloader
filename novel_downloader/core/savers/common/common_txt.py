#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.common_saver.qidian_txt
----------------------------------------------------

Contains the logic for exporting novel content as a single `.txt` file.

This module defines `common_save_as_txt` function, which assembles and formats
a novel based on metadata and chapter files found in the raw data directory.
It is intended to be used by `CommonSaver` as part of the save/export process.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from novel_downloader.utils.file_utils import save_as_txt
from novel_downloader.utils.text_utils import clean_chapter_title, format_chapter

if TYPE_CHECKING:
    from .main_saver import CommonSaver

logger = logging.getLogger(__name__)

CHAPTER_FOLDERS: List[str] = [
    "chapters",
    "encrypted_chapters",
]


def _find_chapter_file(
    raw_base: Path,
    chapter_id: str,
) -> Optional[Path]:
    """
    Search for `<chapter_id>.json` under each folder in CHAPTER_FOLDERS
    inside raw_data_dir/site/book_id. Return the first existing Path,
    or None if not found.
    """
    for folder in CHAPTER_FOLDERS:
        candidate = raw_base / folder / f"{chapter_id}.json"
        if candidate.exists():
            return candidate
    return None


def common_save_as_txt(
    saver: CommonSaver,
    book_id: str,
) -> None:
    """
    将 save_path 文件夹中该小说的所有章节 json 文件合并保存为一个完整的 txt 文件,
    并保存到 out_path 下
    假设章节文件名格式为 `{chapterId}.json`

    处理流程：
      1. 从 book_info.json 中加载书籍信息 (包含书名、作者、简介及卷章节列表)
      2. 遍历各卷, 每个卷先追加卷标题, 然后依次追加该卷下各章节的标题和内容,
         同时记录最后一个章节标题作为“原文截至”
      3. 将书籍元信息 (书名、作者、原文截至、内容简介) 与所有章节内容拼接,
         构成最终完整文本
      4. 将最终结果保存到 out_path 下 (例如：`{book_name}.txt`)

    :param book_id: Identifier of the novel (used as subdirectory name).
    """
    TAG = "[saver]"
    site = saver.site
    # --- Paths & options ---
    raw_base = saver.raw_data_dir / site / book_id
    out_dir = saver.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load book_info.json ---
    info_path = raw_base / "book_info.json"
    try:
        info_text = info_path.read_text(encoding="utf-8")
        book_info = json.loads(info_text)
    except Exception as e:
        logger.error("%s Failed to load %s: %s", TAG, info_path, e)
        return

    # --- Compile chapters ---
    parts: List[str] = []
    latest_chapter: str = ""
    volumes = book_info.get("volumes", [])

    for vol in volumes:
        vol_name = vol.get("volume_name", "").strip()
        vol_name = clean_chapter_title(vol_name)
        if vol_name:
            volume_header = f"\n\n{'=' * 6} {vol_name} {'=' * 6}\n\n"
            parts.append(volume_header)
            logger.info("%s Processing volume: %s", TAG, vol_name)
        for chap in vol.get("chapters", []):
            chap_id = chap.get("chapterId")
            chap_title = chap.get("title", "")
            if not chap_id:
                logger.warning("%s Missing chapterId, skipping: %s", TAG, chap)
                continue

            # Find the JSON file in one of the known subfolders
            json_path = _find_chapter_file(raw_base, chap_id)
            if json_path is None:
                logger.info(
                    "%s Missing chapter file in: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            try:
                chapter_data = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("%s Error reading %s: %s", TAG, json_path, e)
                continue

            # Extract structured fields
            title = chapter_data.get("title", chap_title).strip()
            content = chapter_data.get("content", "").strip()
            author_say = chapter_data.get("author_say", "").strip()
            clean_title = clean_chapter_title(title)

            parts.append(format_chapter(clean_title, content, author_say))
            latest_chapter = clean_title

    # --- Build header ---
    name = book_info.get("book_name")
    author = book_info.get("author")
    words = book_info.get("word_count")
    updated = book_info.get("update_time")
    summary = book_info.get("summary")

    header_lines = []

    if name:
        header_lines.append(f"书名: {name}")

    if author:
        header_lines.append(f"作者: {author}")

    if words:
        header_lines.append(f"总字数: {words}")

    if updated:
        header_lines.append(f"更新日期: {updated}")

    header_lines.append(f"原文截至: {latest_chapter}")

    if summary:
        header_lines.append("内容简介:")
        header_lines.append(summary)

    header_lines.append("")
    header_lines.append("-" * 10)
    header_lines.append("")

    header = "\n".join(header_lines)

    final_text = header + "\n\n" + "\n\n".join(parts).strip()

    # --- Determine output file path ---
    out_name = saver.get_filename(title=name, author=author, ext="txt")
    out_path = out_dir / out_name

    # --- Save final text ---
    try:
        save_as_txt(content=final_text, filepath=out_path)
        logger.info("%s Novel saved to: %s", TAG, out_path)
    except Exception as e:
        logger.error("%s Failed to save file: %s", TAG, e)
    return
