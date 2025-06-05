#!/usr/bin/env python3
"""
novel_downloader.core.exporters.linovelib.epub
----------------------------------------------

Contains the logic for exporting novel content as a single `.epub` file.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ebooklib import epub

from novel_downloader.core.exporters.epub_utils import (
    add_images_from_dir,
    add_images_from_list,
    chapter_txt_to_html,
    create_css_items,
    create_volume_intro,
    init_epub,
)
from novel_downloader.utils.constants import (
    DEFAULT_HEADERS,
    EPUB_IMAGE_FOLDER,
    EPUB_IMAGE_WRAPPER,
    EPUB_OPTIONS,
    EPUB_TEXT_FOLDER,
)
from novel_downloader.utils.file_utils import sanitize_filename
from novel_downloader.utils.network import download_image

if TYPE_CHECKING:
    from .main_exporter import LinovelibExporter

_IMG_TAG_PATTERN = re.compile(
    r'<img\s+[^>]*src=[\'"]([^\'"]+)[\'"][^>]*>', re.IGNORECASE
)
_IMG_HEADERS = DEFAULT_HEADERS.copy()
_IMG_HEADERS["Referer"] = "https://www.linovelib.com/"


def export_whole_book(
    exporter: LinovelibExporter,
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

    :param book_id: Identifier of the novel (used as subdirectory name).
    """
    TAG = "[exporter]"
    config = exporter._config
    # --- Paths & options ---
    raw_base = exporter._raw_data_dir / book_id
    img_dir = exporter._cache_dir / book_id / "images"
    out_dir = exporter.output_dir
    img_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load book_info.json ---
    info_path = raw_base / "book_info.json"
    try:
        info_text = info_path.read_text(encoding="utf-8")
        book_info = json.loads(info_text)
    except Exception as e:
        exporter.logger.error("%s Failed to load %s: %s", TAG, info_path, e)
        return

    book_name = book_info.get("book_name", book_id)
    exporter.logger.info(
        "%s Starting EPUB generation: %s (ID: %s)", TAG, book_name, book_id
    )

    # --- Generate intro + cover ---
    intro_html = _generate_intro_html(book_info)
    cover_path: Path | None = None
    cover_url = book_info.get("cover_url", "")
    if config.include_cover and cover_url:
        cover_path = download_image(
            cover_url,
            raw_base,
            target_name="cover",
            headers=_IMG_HEADERS,
            on_exist="overwrite",
        )
        if not cover_path:
            exporter.logger.warning("Failed to download cover from %s", cover_url)

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
        vol_name = vol.get("volume_name", "").strip() or f"Unknown Volume {vol_index}"
        vol_name = vol_name.replace(book_name, "").strip()
        vol_cover_path: Path | None = None
        vol_cover_url = vol.get("volume_cover", "")
        if config.include_cover and vol_cover_url:
            vol_cover_path = download_image(
                vol_cover_url,
                img_dir,
                headers=_IMG_HEADERS,
                on_exist="skip",
            )

        exporter.logger.info("Processing volume %d: %s", vol_index, vol_name)

        # Volume intro
        vol_intro = epub.EpubHtml(
            title=vol_name,
            file_name=f"{EPUB_TEXT_FOLDER}/volume_intro_{vol_index}.xhtml",
            lang="zh",
        )
        vol_intro.content = _generate_vol_intro_html(
            vol_name,
            vol.get("volume_intro", ""),
            vol_cover_path,
        )
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
                exporter.logger.warning("%s Missing chapterId, skipping: %s", TAG, chap)
                continue

            chapter_data = exporter._get_chapter(book_id, chap_id)
            if not chapter_data:
                exporter.logger.info(
                    "%s Missing chapter file: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            title = chapter_data.get("title", "") or chap_id
            content: str = chapter_data.get("content", "")
            content, _ = _inline_remote_images(content, img_dir)
            chap_html = chapter_txt_to_html(
                chapter_title=title,
                chapter_text=content,
                author_say="",
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
    exporter.logger.info("%s Building TOC and spine...", TAG)
    book.toc = toc_list
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    out_name = exporter.get_filename(
        title=book_name,
        author=book_info.get("author"),
        ext="epub",
    )
    out_path = out_dir / sanitize_filename(out_name)

    try:
        epub.write_epub(out_path, book, EPUB_OPTIONS)
        exporter.logger.info("%s EPUB successfully written to %s", TAG, out_path)
    except Exception as e:
        exporter.logger.error("%s Failed to write EPUB to %s: %s", TAG, out_path, e)
    return


def export_by_volume(
    exporter: LinovelibExporter,
    book_id: str,
) -> None:
    """
    Export a single novel (identified by `book_id`) to multi EPUB file.

    :param book_id: Identifier of the novel (used as subdirectory name).
    """
    TAG = "[exporter]"
    config = exporter._config
    # --- Paths & options ---
    raw_base = exporter._raw_data_dir / book_id
    img_dir = exporter._cache_dir / book_id / "images"
    out_dir = exporter.output_dir
    img_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load book_info.json ---
    info_path = raw_base / "book_info.json"
    try:
        info_text = info_path.read_text(encoding="utf-8")
        book_info = json.loads(info_text)
    except Exception as e:
        exporter.logger.error("%s Failed to load %s: %s", TAG, info_path, e)
        return

    book_name = book_info.get("book_name", book_id)
    exporter.logger.info(
        "%s Starting EPUB generation: %s (ID: %s)", TAG, book_name, book_id
    )
    css_items = create_css_items(
        include_main=True,
        include_volume=True,
    )

    # --- Compile columes ---
    volumes = book_info.get("volumes", [])
    for vol_index, vol in enumerate(volumes, start=1):
        vol_name = vol.get("volume_name", "").strip() or f"Unknown Volume {vol_index}"
        vol_cover_path: Path | None = None
        vol_cover_url = vol.get("volume_cover", "")
        if config.include_cover and vol_cover_url:
            vol_cover_path = download_image(
                vol_cover_url,
                img_dir,
                headers=_IMG_HEADERS,
                on_exist="skip",
            )
        intro_html = _generate_intro_html(vol)

        book, spine, toc_list = init_epub(
            book_info=vol,
            book_id=f"{book_id}_{vol_index}",
            intro_html=intro_html,
            book_cover_path=vol_cover_path,
            include_toc=config.include_toc,
        )
        for css in css_items:
            book.add_item(css)

        for chap in vol.get("chapters", []):
            chap_id = chap.get("chapterId")
            chap_title = chap.get("title", "")
            if not chap_id:
                exporter.logger.warning("%s Missing chapterId, skipping: %s", TAG, chap)
                continue

            chapter_data = exporter._get_chapter(book_id, chap_id)
            if not chapter_data:
                exporter.logger.info(
                    "%s Missing chapter file: %s (%s), skipping.",
                    TAG,
                    chap_title,
                    chap_id,
                )
                continue

            title = chapter_data.get("title", "") or chap_id
            content: str = chapter_data.get("content", "")
            content, imgs = _inline_remote_images(content, img_dir)
            chap_html = chapter_txt_to_html(
                chapter_title=title,
                chapter_text=content,
                author_say="",
            )
            add_images_from_list(book, imgs)

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
            toc_list.append(item)

        book.toc = toc_list
        book.spine = spine
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        out_name = exporter.get_filename(
            title=vol_name,
            author=book_info.get("author"),
            ext="epub",
        )
        out_path = out_dir / sanitize_filename(out_name)

        try:
            epub.write_epub(out_path, book, EPUB_OPTIONS)
            exporter.logger.info("%s EPUB successfully written to %s", TAG, out_path)
        except Exception as e:
            exporter.logger.error("%s Failed to write EPUB to %s: %s", TAG, out_path, e)
    return


def _generate_intro_html(
    info: dict[str, Any],
    default_author: str = "",
) -> str:
    """
    Generate an HTML snippet containing book metadata and summary.

    :param info: A dict that may contain book info
    :param default_author: Fallback author name.

    :return: An HTML-formatted string.
    """
    title = info.get("book_name") or info.get("volume_name")
    author = info.get("author") or default_author
    status = info.get("serial_status")
    words = info.get("word_count")
    raw_summary = (info.get("summary") or info.get("volume_intro") or "").strip()

    html_parts = [
        "<h1>书籍简介</h1>",
        '<div class="list">',
        "<ul>",
    ]
    metadata = [
        ("书名", title),
        ("作者", author),
        ("状态", status),
        ("字数", words),
    ]
    for label, value in metadata:
        if value is not None and str(value).strip():
            safe = html.escape(str(value))
            if label == "书名":
                safe = f"《{safe}》"
            html_parts.append(f"<li>{label}: {safe}</li>")

    html_parts.extend(["</ul>", "</div>"])

    if raw_summary:
        html_parts.append('<p class="new-page-after"><br/></p>')
        html_parts.append("<h2>简介</h2>")
        for para in filter(None, (p.strip() for p in raw_summary.split("\n\n"))):
            safe_para = html.escape(para).replace("\n", "<br/>")
            html_parts.append(f"<p>{safe_para}</p>")

    return "\n".join(html_parts)


def _generate_vol_intro_html(
    title: str,
    intro: str = "",
    cover_path: Path | None = None,
) -> str:
    """
    Generate the HTML snippet for a volume's introduction section.

    :param title: Title of the volume.
    :param intro: Optional introduction text for the volume.
    :param cover_path: Path of the volume cover.
    :return: HTML string representing the volume's intro section.
    """
    if cover_path is None:
        return create_volume_intro(title, intro)

    html_parts = [
        f'<h1 class="volume-title-line1">{title}</h1>',
        f'<img class="width100" src="../{EPUB_IMAGE_FOLDER}/{cover_path.name}" />',
        '<p class="new-page-after"><br/></p>',
    ]

    if intro.strip():
        html_parts.append(f'<p class="intro">{intro}</p>')

    return "\n".join(html_parts)


def _inline_remote_images(
    content: str,
    image_dir: str | Path,
) -> tuple[str, list[Path]]:
    """
    Download every remote `<img src="...">` in `content` into `image_dir`,
    and replace the original tag with EPUB_IMAGE_WRAPPER
    pointing to the local filename.

    :param content: HTML/text of the chapter containing <img> tags.
    :param image_dir: Directory to save downloaded images into.
    :return: A tuple (modified_content, list_of_downloaded_image_paths).
    """
    downloaded_images: list[Path] = []

    def _replace(match: re.Match[str]) -> str:
        url = match.group(1)
        try:
            # download_image returns a Path or None
            local_path = download_image(
                url,
                image_dir,
                target_name=None,
                headers=_IMG_HEADERS,
                on_exist="skip",
            )
            if not local_path:
                return match.group(0)

            downloaded_images.append(local_path)
            return EPUB_IMAGE_WRAPPER.format(filename=local_path.name)
        except Exception:
            return match.group(0)

    modified_content = _IMG_TAG_PATTERN.sub(_replace, content)
    return modified_content, downloaded_images
