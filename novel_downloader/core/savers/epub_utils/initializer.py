#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.epub_utils.initializer

Initializes an epub.EpubBook object, sets metadata
(identifier, title, author, language, description),
adds a cover, and prepares the initial spine and TOC entries.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ebooklib import epub

from novel_downloader.utils.constants import (
    EPUB_IMAGE_FOLDER,
    EPUB_TEXT_FOLDER,
    VOLUME_BORDER_IMAGE_PATH,
)

logger = logging.getLogger(__name__)


def init_epub(
    book_info: Dict[str, Any],
    book_id: str,
    intro_html: str,
    book_cover_path: Optional[Path] = None,
    include_toc: bool = False,
) -> Tuple[epub.EpubBook, List[Any], List[Any]]:
    """
    Initialize an EPUB book with metadata, optional cover, and intro page.

    :param book_info: Dict with keys 'book_name', 'author', 'summary'.
    :param book_id: Book identifier (numeric or string).
    :param intro_html: Intro content in XHTML format.
    :param book_cover_path: Optional Path to the cover image file.
    :param include_toc: Whether to include the <nav> item in the spine.
    :return: (book, spine, toc_list)
    """
    book = epub.EpubBook()
    book.set_identifier(str(book_id))
    book.set_title(book_info.get("book_name", "未找到书名"))
    book.set_language("zh-CN")
    book.add_author(book_info.get("author", "未找到作者"))
    book.add_metadata("DC", "description", book_info.get("summary", "未找到作品简介"))

    spine = []

    # cover
    if book_cover_path:
        try:
            cover_bytes = book_cover_path.read_bytes()
            ext = book_cover_path.suffix.lower()
            ext = ext if ext in [".jpg", ".jpeg", ".png"] else ".jpeg"
            filename = f"{EPUB_IMAGE_FOLDER}/cover{ext}"
            book.set_cover(filename, cover_bytes)
            spine.append("cover")
        except FileNotFoundError:
            logger.info(f"[epub] 封面图片不存在: {book_cover_path}")
        except Exception as e:
            logger.info(f"[epub] 读取封面失败: {book_cover_path}，错误：{e}")

    # 导航菜单
    if include_toc:
        spine.append("nav")

    # 简介页面
    intro = epub.EpubHtml(
        title="书籍简介",
        file_name=f"{EPUB_TEXT_FOLDER}/intro.xhtml",
        lang="zh-CN",
        uid="intro",
    )
    intro.content = intro_html
    intro.add_link(href="../Styles/main.css", rel="stylesheet", type="text/css")
    book.add_item(intro)
    spine.append(intro)

    # 添加卷边框图像 (volume_border.png)
    try:
        border_bytes = VOLUME_BORDER_IMAGE_PATH.read_bytes()
        border_item = epub.EpubItem(
            uid="volume-border",
            file_name=f"{EPUB_IMAGE_FOLDER}/volume_border.png",
            media_type="image/png",
            content=border_bytes,
        )
        book.add_item(border_item)
    except FileNotFoundError:
        logger.info(f"[epub] 卷边框图片不存在: {VOLUME_BORDER_IMAGE_PATH}")
    except Exception as e:
        logger.info(f"[epub] 读取卷边框失败: {VOLUME_BORDER_IMAGE_PATH}: {e}")

    toc_list = [epub.Link(intro.file_name, "书籍简介", intro.id)]
    return book, spine, toc_list
