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
    Generate HTML string for a book's information and summary.

    :return: An HTML-formatted string presenting the book's information.
    """
    root = html.Element("div")

    title_el = etree.SubElement(root, "h1")
    title_el.text = "书籍简介"

    div_list = etree.SubElement(root, "div", {"class": "list"})
    ul = etree.SubElement(div_list, "ul")

    _add_li(ul, "书名", f"《{book_name}》" if book_name else "")
    _add_li(ul, "作者", author)
    _add_li(ul, "分类", ", ".join(subject) if subject else "")
    _add_li(ul, "字数", word_count)
    _add_li(ul, "状态", serial_status)

    if summary:
        etree.SubElement(root, "p", {"class": "new-page-after"}).text = ""
        etree.SubElement(root, "h2").text = "简介"
        for line in summary.split("\n"):
            line = line.strip()
            if line:
                p = etree.SubElement(root, "p")
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
    Generate the HTML snippet for a volume's introduction section.

    :param volume_title: Title of the volume.
    :param volume_intro_text: Optional introduction text for the volume.
    :return: HTML string representing the volume's intro section.
    """
    root = html.Element("div")

    line1, line2 = _split_volume_title(volume_title)

    root.append(_make_vol_border_img("border1"))

    h1 = etree.SubElement(root, "h1", {"class": "volume-title-line1"})
    h1.text = line1

    root.append(_make_vol_border_img("border2"))

    if line2:
        p_line2 = etree.SubElement(root, "p", {"class": "volume-title-line2"})
        p_line2.text = line2

    if volume_intro_text:
        for line in volume_intro_text.split("\n"):
            line = line.strip()
            if line:
                p = etree.SubElement(root, "p", {"class": "intro"})
                p.text = line

    html_string: str = html.tostring(
        root,
        pretty_print=PRETTY_PRINT_FLAG,
        encoding="unicode",
    )
    return html_string


def _add_li(ul: etree._Element, label: str, value: str) -> None:
    if value:
        li = etree.SubElement(ul, "li")
        li.text = f"{label}: {value}"


def _make_vol_border_img(class_name: str) -> html.HtmlElement:
    div = html.Element("div", {"class": class_name})
    etree.SubElement(
        div,
        "img",
        {
            "alt": "",
            "class": class_name,
            "src": f"../{IMAGE_FOLDER}/volume_border.png",
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
        parts = volume_title.split(" ")
    elif "-" in volume_title:
        parts = volume_title.split("-")
    else:
        return volume_title, ""

    return parts[0], "".join(parts[1:])
