#!/usr/bin/env python3
"""
novel_downloader.core.exporters.epub_util
-----------------------------------------

Utilities for preparing and formatting chapter HTML for EPUB exports.
"""

__all__ = [
    "download_cover",
    "prepare_builder",
    "finalize_export",
    "inline_remote_images",
    "build_epub_chapter",
]

import html
import logging
import re
from pathlib import Path

from novel_downloader.utils import download, sanitize_filename
from novel_downloader.utils.constants import (
    CSS_MAIN_PATH,
    DEFAULT_HEADERS,
    DEFAULT_IMAGE_SUFFIX,
)
from novel_downloader.utils.epub import EpubBuilder, StyleSheet

_IMAGE_WRAPPER = (
    '<div class="duokan-image-single illus"><img src="../Images/{filename}" /></div>'
)
_IMG_TAG_PATTERN = re.compile(
    r'<img\s+[^>]*src=[\'"]([^\'"]+)[\'"][^>]*>', re.IGNORECASE
)
_RAW_HTML_RE = re.compile(
    r'^(<img\b[^>]*?\/>|<div class="duokan-image-single illus">.*?<\/div>)$', re.DOTALL
)


def download_cover(
    cover_url: str,
    raw_base: Path,
    include_cover: bool,
    logger: logging.Logger,
    tag: str,
    headers: dict[str, str] | None = None,
) -> Path | None:
    if include_cover and cover_url:
        path = download(
            cover_url,
            raw_base,
            filename="cover",
            headers=headers or DEFAULT_HEADERS,
            on_exist="overwrite",
            default_suffix=DEFAULT_IMAGE_SUFFIX,
        )
        if not path:
            logger.warning("%s Failed to download cover from %s", tag, cover_url)
        return path
    return None


def prepare_builder(
    site_name: str,
    book_id: str,
    title: str,
    author: str,
    description: str,
    subject: list[str],
    serial_status: str,
    word_count: str,
    cover_path: Path | None,
) -> tuple[EpubBuilder, StyleSheet]:
    book = EpubBuilder(
        title=title,
        author=author,
        description=description,
        cover_path=cover_path,
        subject=subject,
        serial_status=serial_status,
        word_count=word_count,
        uid=f"{site_name}_{book_id}",
    )
    css_text = CSS_MAIN_PATH.read_text(encoding="utf-8")
    main_css = StyleSheet(id="main_style", content=css_text, filename="main.css")
    book.add_stylesheet(main_css)
    return book, main_css


def finalize_export(
    book: EpubBuilder,
    out_dir: Path,
    filename: str,
    logger: logging.Logger,
    tag: str,
) -> None:
    out_path = out_dir / sanitize_filename(filename)
    try:
        book.export(out_path)
        logger.info("%s EPUB successfully written to %s", tag, out_path)
    except OSError as e:
        logger.error("%s Failed to write EPUB to %s: %s", tag, out_path, e)


def inline_remote_images(
    book: EpubBuilder,
    content: str,
    image_dir: Path,
    headers: dict[str, str] | None = None,
) -> str:
    """
    Download every remote `<img src="...">` in `content` into `image_dir`,
    and replace the original tag with _IMAGE_WRAPPER.

    :param content: HTML/text of the chapter containing <img> tags.
    :param image_dir: Directory to save downloaded images into.
    :return: modified_content.
    """

    def _replace(match: re.Match[str]) -> str:
        url = match.group(1)
        try:
            local_path = download(
                url,
                image_dir,
                headers=headers or DEFAULT_HEADERS,
                on_exist="skip",
                default_suffix=DEFAULT_IMAGE_SUFFIX,
            )
            if not local_path:
                return match.group(0)
            filename = book.add_image(local_path)
            return _IMAGE_WRAPPER.format(filename=filename)
        except Exception:
            return match.group(0)

    modified_content = _IMG_TAG_PATTERN.sub(_replace, content)
    return modified_content


def build_epub_chapter(
    title: str,
    paragraphs: str,
    extras: dict[str, str] | None = None,
) -> str:
    """
    Build a formatted chapter epub HTML including title, body paragraphs,
    and optional extra sections.

    :param title:      Chapter title.
    :param paragraphs: Raw multi-line string. Blank lines are ignored.
    :param extras:     Optional dict mapping section titles to multi-line strings.
    :return:           A HTML include title, paragraphs, and extras.
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
    parts.append(f"<h2>{html.escape(title)}</h2>")
    parts.append(_render_block(paragraphs))

    if extras:
        for title, note in extras.items():
            note = note.strip()
            if not note:
                continue
            parts.extend(
                [
                    "<hr />",
                    f"<h3>{html.escape(title)}</h3>",
                    _render_block(note),
                ]
            )

    return "\n".join(parts)
