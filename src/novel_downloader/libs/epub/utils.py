#!/usr/bin/env python3
"""
novel_downloader.libs.epub.utils
--------------------------------

Pure utility functions for EPUB assembly, including:
  * Computing file hashes
  * Generating META-INF/container.xml
  * Constructing HTML snippets for the book intro and volume intro
"""

import hashlib
from html import escape
from pathlib import Path

from .constants import (
    CONTAINER_TEMPLATE,
    IMAGE_FOLDER,
    ROOT_PATH,
)


def hash_file(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 hash of a file.

    :param file_path: The Path object of the file to hash.
    :param chunk_size: The chunk size to read the file (default: 8192).
    :return: The SHA256 hash string (lowercase hex) of the file content.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def build_container_xml(
    root_path: str = ROOT_PATH,
) -> str:
    """
    Generate the XML content for META-INF/container.xml in an EPUB archive.

    :param root_path: The folder where the OPF file is stored.
    :return: A string containing the full XML for container.xml.
    """
    return CONTAINER_TEMPLATE.format(root_path=root_path)


def build_book_intro(
    book_name: str,
    author: str,
    serial_status: str,
    subject: list[str],
    word_count: str,
    summary: str,
) -> str:
    """
    Build the HTML snippet for the overall book introduction.

    This includes:
      * A main heading ("Book Introduction")
      * A list of metadata items (title, author, categories, word count, status)
      * A "Summary" subheading and one or more paragraphs of summary text

    :return: A HTML string for inclusion in `intro.xhtml`
    """
    lines = []

    lines.append("<div>")
    lines.append("<h1>书籍简介</h1>")
    lines.append('<div class="intro-info">')
    lines.append("<ul>")

    name_val = f"《{book_name}》" if book_name else ""
    subj_val = ", ".join(subject) if subject else ""

    li_lines = [
        _li_line("书名", name_val),
        _li_line("作者", author),
        _li_line("分类", subj_val),
        _li_line("字数", word_count),
        _li_line("状态", serial_status),
    ]
    for li in li_lines:
        if li:
            lines.append(li)

    lines.append("</ul>")
    lines.append("</div>")

    if summary:
        lines.append('<p class="new-page-after"></p>')
        lines.append("<h2>简介</h2>")
        lines.append('<div class="intro-summary">')
        for line in summary.splitlines():
            s = line.strip()
            if not s:
                continue
            lines.append(f"<p>{escape(s, quote=True)}</p>")
        lines.append("</div>")

    lines.append("</div>")
    return "\n".join(lines)


def build_volume_intro(
    volume_title: str,
    volume_intro_text: str = "",
) -> str:
    """
    Build the HTML snippet for a single-volume introduction.

    This includes:
      * A decorative border image (top and bottom)
      * A primary heading (volume main title)
      * An optional secondary line (subtitle)
      * One or more paragraphs of intro text

    :param volume_title: e.g. "Volume 1 - The Beginning"
    :param volume_intro_text: multiline intro text for this volume
    :return: A HTML string for inclusion in `vol_<n>.xhtml`
    """
    line1, line2 = _split_volume_title(volume_title)

    lines = []
    lines.append("<div>")
    lines.append('<div class="vol-header">')
    lines.append(_vol_border_div_str(flip=False))
    lines.append(f'<h1 class="vol-title-main">{escape(line1, quote=True)}</h1>')
    lines.append(_vol_border_div_str(flip=True))
    if line2:
        lines.append(f'<h2 class="vol-title-sub">{escape(line2, quote=True)}</h2>')
    lines.append("</div>")

    if volume_intro_text:
        lines.append('<p class="new-page-after"></p>')
        lines.append('<div class="vol-intro-text">')
        for line in volume_intro_text.splitlines():
            s = line.strip()
            if not s:
                continue
            lines.append(f"<p>{escape(s, quote=True)}</p>")
        lines.append("</div>")

    lines.append("</div>")
    return "\n".join(lines)


def _li_line(label: str, value: str) -> str:
    if not value:
        return ""
    return f"<li>{escape(label, quote=True)}: {escape(value, quote=True)}</li>"


def _vol_border_div_str(flip: bool = False) -> str:
    classes = "vol-border" + (" flip" if flip else "")
    return (
        f'<div class="{classes}">'
        f'<img src="../{IMAGE_FOLDER}/volume_border.png" alt="" />'
        f"</div>"
    )


def _split_volume_title(volume_title: str) -> tuple[str, str]:
    """
    Split volume title into two parts for better display.

    :param volume_title: Original volume title string.
    :return: Tuple of (line1, line2)
    """
    if "-" in volume_title:
        parts = volume_title.split("-", 1)
    elif " " in volume_title:
        parts = volume_title.split(" ", 1)
    else:
        return volume_title, ""

    return parts[0], parts[1]
