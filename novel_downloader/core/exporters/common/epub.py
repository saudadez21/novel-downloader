#!/usr/bin/env python3
"""
novel_downloader.core.exporters.common.epub
-------------------------------------------

Contains the logic for exporting novel content as a single `.epub` file.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from novel_downloader.core.exporters.epub_util import (
    Book,
    Chapter,
    StyleSheet,
    Volume,
)
from novel_downloader.utils.constants import CSS_MAIN_PATH
from novel_downloader.utils.file_utils import sanitize_filename
from novel_downloader.utils.network import download_image
from novel_downloader.utils.text_utils import clean_chapter_title

if TYPE_CHECKING:
    from .main_exporter import CommonExporter

_IMAGE_WRAPPER = (
    '<div class="duokan-image-single illus"><img src="../Images/{filename}" /></div>'
)
_IMG_TAG_PATTERN = re.compile(
    r'<img\s+[^>]*src=[\'"]([^\'"]+)[\'"][^>]*>', re.IGNORECASE
)
_RAW_HTML_RE = re.compile(
    r'^(<img\b[^>]*?\/>|<div class="duokan-image-single illus">.*?<\/div>)$', re.DOTALL
)


def common_export_as_epub(
    exporter: CommonExporter,
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
    book_author = book_info.get("author", "")
    exporter.logger.info(
        "%s Starting EPUB generation: %s (ID: %s)", TAG, book_name, book_id
    )

    # --- Generate intro + cover ---
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
            exporter.logger.warning("Failed to download cover from %s", cover_url)

    # --- Initialize EPUB ---
    book = Book(
        title=book_name,
        author=book_author,
        description=book_info.get("summary", ""),
        cover_path=cover_path,
        subject=book_info.get("subject", []),
        serial_status=book_info.get("serial_status", ""),
        word_count=book_info.get("word_count", ""),
        uid=f"{exporter.site}_{book_id}",
    )
    main_css = StyleSheet(
        id="main_style",
        content=CSS_MAIN_PATH.read_text(encoding="utf-8"),
        filename="main.css",
    )
    book.add_stylesheet(main_css)

    # --- Compile chapters ---
    volumes = book_info.get("volumes", [])
    for vol_index, vol in enumerate(volumes, start=1):
        raw_vol_name = vol.get("volume_name", "")
        raw_vol_name = raw_vol_name.replace(book_name, "").strip()
        vol_name = raw_vol_name or f"Volume {vol_index}"
        exporter.logger.info("Processing volume %d: %s", vol_index, vol_name)

        vol_cover_path: Path | None = None
        vol_cover_url = vol.get("volume_cover", "")
        if vol_cover_url:
            vol_cover_path = download_image(
                vol_cover_url,
                img_dir,
                on_exist="skip",
            )

        curr_vol = Volume(
            id=f"vol_{vol_index}",
            title=vol_name,
            intro=vol.get("volume_intro", ""),
            cover=vol_cover_path,
        )

        for chap in vol.get("chapters", []):
            chap_id = chap.get("chapterId")
            chap_title = chap.get("title", "")
            if not chap_id:
                exporter.logger.warning(
                    "%s Missing chapterId, skipping: %s",
                    TAG,
                    chap,
                )
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

            title = clean_chapter_title(chapter_data.get("title", "")) or chap_id
            content: str = chapter_data.get("content", "")
            content, img_paths = _inline_remote_images(content, img_dir)
            chap_html = _txt_to_html(
                chapter_title=title,
                chapter_text=content,
                extras={
                    "作者说": chapter_data.get("author_say", ""),
                },
            )
            curr_vol.add_chapter(
                Chapter(
                    id=f"c_{chap_id}",
                    title=title,
                    content=chap_html,
                    css=[main_css],
                )
            )
            for img_path in img_paths:
                book.add_image(img_path)

        book.add_volume(curr_vol)

    # --- 5. Finalize EPUB ---
    out_name = exporter.get_filename(
        title=book_name,
        author=book_info.get("author"),
        ext="epub",
    )
    out_path = out_dir / sanitize_filename(out_name)

    try:
        book.export(out_path)
        exporter.logger.info("%s EPUB successfully written to %s", TAG, out_path)
    except Exception as e:
        exporter.logger.error("%s Failed to write EPUB to %s: %s", TAG, out_path, e)
    return


def _inline_remote_images(
    content: str,
    image_dir: str | Path,
) -> tuple[str, list[Path]]:
    """
    Download every remote `<img src="...">` in `content` into `image_dir`,
    and replace the original tag with _IMAGE_WRAPPER
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
                on_exist="skip",
            )
            if not local_path:
                return match.group(0)

            downloaded_images.append(local_path)
            return _IMAGE_WRAPPER.format(filename=local_path.name)
        except Exception:
            return match.group(0)

    modified_content = _IMG_TAG_PATTERN.sub(_replace, content)
    return modified_content, downloaded_images


def _txt_to_html(
    chapter_title: str,
    chapter_text: str,
    extras: dict[str, str] | None = None,
) -> str:
    """
    Convert chapter text and author note to styled HTML.

    :param chapter_title: Title of the chapter.
    :param chapter_text: Main content of the chapter.
    :param extras: Optional dict of titles and content, e.g. {"作者说": "text"}.
    :return: Rendered HTML as a string.
    """

    def _render_block(text: str) -> str:
        lines = (line.strip() for line in text.splitlines() if line.strip())
        out = []
        for line in lines:
            # preserve raw HTML, otherwise wrap in <p>
            if _RAW_HTML_RE.match(line):
                out.append(line)
            else:
                out.append(f"<p>{html.escape(line)}</p>")
        return "\n".join(out)

    parts = []
    parts.append(f"<h2>{html.escape(chapter_title)}</h2>")
    parts.append(_render_block(chapter_text))

    if extras:
        for title, note in extras.items():
            note = note.strip()
            if not note:
                continue
            parts.extend(
                [
                    "<hr />",
                    f"<p>{html.escape(title)}</p>",
                    _render_block(note),
                ]
            )

    return "\n".join(parts)
