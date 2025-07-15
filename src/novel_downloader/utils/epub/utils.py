#!/usr/bin/env python3
"""
novel_downloader.utils.epub.utils
---------------------------------

Pure utility functions for EPUB assembly, including:
- Computing file hashes
- Generating META-INF/container.xml
- Constructing HTML snippets for the book intro and volume intro
"""

import hashlib
from pathlib import Path

from lxml import etree, html

from .constants import (
    CONTAINER_TEMPLATE,
    IMAGE_FOLDER,
    PRETTY_PRINT_FLAG,
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
      - A main heading ("Book Introduction")
      - A list of metadata items (title, author, categories, word count, status)
      - A "Summary" subheading and one or more paragraphs of summary text

    :return: A HTML string for inclusion in `intro.xhtml`
    """
    root = html.Element("div")

    # Main heading
    h1 = etree.SubElement(root, "h1")
    h1.text = "书籍简介"

    # Metadata list
    info_div = etree.SubElement(root, "div", {"class": "intro-info"})
    ul = etree.SubElement(info_div, "ul")
    _add_li(ul, "书名", f"《{book_name}》" if book_name else "")
    _add_li(ul, "作者", author)
    _add_li(ul, "分类", ", ".join(subject) if subject else "")
    _add_li(ul, "字数", word_count)
    _add_li(ul, "状态", serial_status)

    # Summary section
    if summary:
        # force page break before summary
        etree.SubElement(root, "p", {"class": "new-page-after"})
        h2 = etree.SubElement(root, "h2")
        h2.text = "简介"

        summary_div = etree.SubElement(root, "div", {"class": "intro-summary"})
        for line in summary.splitlines():
            line = line.strip()
            if not line:
                continue
            p = etree.SubElement(summary_div, "p")
            p.text = line

    html_string: str = html.tostring(
        root,
        pretty_print=PRETTY_PRINT_FLAG,
        encoding="unicode",
    )
    return html_string


def build_volume_intro(
    volume_title: str,
    volume_intro_text: str = "",
) -> str:
    """
    Build the HTML snippet for a single-volume introduction.

    This includes:
      - A decorative border image (top and bottom)
      - A primary heading (volume main title)
      - An optional secondary line (subtitle)
      - One or more paragraphs of intro text

    :param volume_title: e.g. "Volume 1 - The Beginning"
    :param volume_intro_text: multiline intro text for this volume
    :return: A HTML string for inclusion in `vol_<n>.xhtml`
    """
    root = html.Element("div")

    # Break the title into two lines if possible
    line1, line2 = _split_volume_title(volume_title)

    header = etree.SubElement(root, "div", {"class": "vol-header"})

    # Top decorative border
    header.append(_make_vol_border_img(flip=False))

    # Main title
    h1 = etree.SubElement(header, "h1", {"class": "vol-title-main"})
    h1.text = line1

    # Bottom decorative border (flipped)
    header.append(_make_vol_border_img(flip=True))

    # Subtitle (if any)
    if line2:
        h2 = etree.SubElement(header, "h2", {"class": "vol-title-sub"})
        h2.text = line2

    # Intro text paragraphs
    if volume_intro_text:
        etree.SubElement(root, "p", {"class": "new-page-after"})

        vol_div = etree.SubElement(root, "div", {"class": "vol-intro-text"})
        for line in volume_intro_text.splitlines():
            line = line.strip()
            if not line:
                continue
            p = etree.SubElement(vol_div, "p")
            p.text = line

    html_string: str = html.tostring(
        root,
        pretty_print=PRETTY_PRINT_FLAG,
        encoding="unicode",
    )
    return html_string


def _add_li(ul: etree._Element, label: str, value: str) -> None:
    """
    Append a `<li>` with 'label: value' if value is nonempty.
    """
    if value:
        li = etree.SubElement(ul, "li")
        li.text = f"{label}: {value}"


def _make_vol_border_img(flip: bool = False) -> html.HtmlElement:
    """
    Return a `<div>` containing the `volume_border.png` image,
    styled by the given class name.
    """
    classes = ["vol-border"]
    if flip:
        classes.append("flip")
    cls = " ".join(classes)

    div = html.Element("div", {"class": cls})
    etree.SubElement(
        div,
        "img",
        {
            "src": f"../{IMAGE_FOLDER}/volume_border.png",
            "alt": "",
        },
    )
    return div


def _split_volume_title(volume_title: str) -> tuple[str, str]:
    """
    Split volume title into two parts for better display.

    :param volume_title: Original volume title string.
    :return: Tuple of (line1, line2)
    """
    if " " in volume_title:
        parts = volume_title.split(" ", 1)
    elif "-" in volume_title:
        parts = volume_title.split("-", 1)
    else:
        return volume_title, ""

    return parts[0], parts[1]
