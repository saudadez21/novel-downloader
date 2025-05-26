#!/usr/bin/env python3
"""
novel_downloader.core.savers.common.epub
----------------------------------------

Contains the logic for exporting novel content as a single `.epub` file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from ebooklib import epub

from novel_downloader.core.savers.epub_utils import (
    add_images_from_dir,
    chapter_txt_to_html,
    create_css_items,
    create_volume_intro,
    generate_book_intro_html,
    init_epub,
    inline_remote_images,
)
from novel_downloader.utils.constants import (
    EPUB_OPTIONS,
    EPUB_TEXT_FOLDER,
)
from novel_downloader.utils.file_utils import sanitize_filename
from novel_downloader.utils.network import download_image
from novel_downloader.utils.text_utils import clean_chapter_title

if TYPE_CHECKING:
    from .main_saver import CommonSaver


def common_save_as_epub(
    saver: CommonSaver,
    book_id: str,
) -> None:
    """
    Export a single novel (identified by `book_id`) to an EPUB file.

    This function will:
      1. Load `book_info.json` for metadata.
      2. Generate introductory HTML and optionally include the cover image.
      3. Initialize the EPUB container.
      4. Iterate through volumes and chapters, convert each to XHTML.
      5. Assemble the spine, TOC, CSS and write out the final `.epub`.

    :param saver: The saver instance, carrying config and path info.
    :param book_id: Identifier of the novel (used as subdirectory name).
    """
    TAG = "[saver]"
    config = saver._config
    # --- Paths & options ---
    raw_base = saver._raw_data_dir / book_id
    img_dir = saver._cache_dir / book_id / "images"
    out_dir = saver.output_dir
    img_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load book_info.json ---
    info_path = raw_base / "book_info.json"
    try:
        info_text = info_path.read_text(encoding="utf-8")
        book_info = json.loads(info_text)
    except Exception as e:
        saver.logger.error("%s Failed to load %s: %s", TAG, info_path, e)
        return

    book_name = book_info.get("book_name", book_id)
    saver.logger.info(
        "%s Starting EPUB generation: %s (ID: %s)", TAG, book_name, book_id
    )

    # --- Generate intro + cover ---
    intro_html = generate_book_intro_html(book_info)
    cover_path: Path | None = None
    cover_url = book_info.get("cover_url", "")
    if config.include_cover and cover_url:
        cover_path = download_image(
            cover_url,
            raw_base,
            target_name="cover",
            on_exist="overwrite",
        )
        if not cover_path:
            saver.logger.warning("Failed to download cover from %s", cover_url)

    # --- Initialize EPUB ---
    book, spine, toc_list = init_epub(
        book_info=book_info,
        book_id=book_id,
        intro_html=intro_html,
        book_cover_path=cover_path,
        include_toc=config.include_toc,
    )
    for css in create_css_items(
        include_main=True,
        include_volume=True,
    ):
        book.add_item(css)

    # --- Compile chapters ---
    volumes = book_info.get("volumes", [])
    for vol_index, vol in enumerate(volumes, start=1):
        raw_vol_name = vol.get("volume_name", "").strip()
        vol_name = clean_chapter_title(raw_vol_name) or f"Unknown Volume {vol_index}"
        saver.logger.info("Processing volume %d: %s", vol_index, vol_name)

        # Volume intro
        vol_intro = epub.EpubHtml(
            title=vol_name,
            file_name=f"{EPUB_TEXT_FOLDER}/volume_intro_{vol_index}.xhtml",
            lang="zh",
        )
        vol_intro.content = create_volume_intro(vol_name, vol.get("volume_intro", ""))
        vol_intro.add_link(
            href="../Styles/volume-intro.css",
            rel="stylesheet",
            type="text/css",
        )
        book.add_item(vol_intro)
        spine.append(vol_intro)

        section = epub.Section(vol_name, vol_intro.file_name)
        chapter_items: list[epub.EpubHtml] = []

        for chap in vol.get("chapters", []):
            chap_id = chap.get("chapterId")
            chap_title = chap.get("title", "")
            if not chap_id:
                saver.logger.warning("%s Missing chapterId, skipping: %s", TAG, chap)
                continue

            chapter_data = saver._get_chapter(book_id, chap_id)
            if not chapter_data:
                saver.logger.info(
                    "%s Missing chapter file: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            title = clean_chapter_title(chapter_data.get("title", "")) or chap_id
            content: str = chapter_data.get("content", "")
            content = inline_remote_images(content, img_dir)
            chap_html = chapter_txt_to_html(
                chapter_title=title,
                chapter_text=content,
                author_say=chapter_data.get("author_say", ""),
            )

            chap_path = f"{EPUB_TEXT_FOLDER}/{chap_id}.xhtml"
            item = epub.EpubHtml(title=chap_title, file_name=chap_path, lang="zh")
            item.content = chap_html
            item.add_link(
                href="../Styles/main.css",
                rel="stylesheet",
                type="text/css",
            )
            book.add_item(item)
            spine.append(item)
            chapter_items.append(item)

        toc_list.append((section, chapter_items))

    book = add_images_from_dir(book, img_dir)

    # --- 5. Finalize EPUB ---
    saver.logger.info("%s Building TOC and spine...", TAG)
    book.toc = toc_list
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    out_name = saver.get_filename(
        title=book_name,
        author=book_info.get("author"),
        ext="epub",
    )
    out_path = out_dir / sanitize_filename(out_name)

    try:
        epub.write_epub(out_path, book, EPUB_OPTIONS)
        saver.logger.info("%s EPUB successfully written to %s", TAG, out_path)
    except Exception as e:
        saver.logger.error("%s Failed to write EPUB to %s: %s", TAG, out_path, e)
    return
