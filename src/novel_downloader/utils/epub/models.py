#!/usr/bin/env python3
"""
novel_downloader.utils.epub.models
----------------------------------

Defines the core EPUB data models and resource classes used by the builder:
- Typed entries for table of contents (ChapterEntry, VolumeEntry)
- Manifest and spine record types (ManifestEntry, SpineEntry)
- Hierarchical NavPoint for NCX navigation
- Base resource class (EpubResource) and specializations:
    - StyleSheet
    - ImageResource
    - Chapter (with XHTML serialization)
- Volume container for grouping chapters with optional intro and cover
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree, html
from lxml.builder import ElementMaker

from .constants import (
    CHAP_DOC_TYPE,
    CSS_FOLDER,
    EPUB_NS,
    PRETTY_PRINT_FLAG,
    XHTML_NS,
    XML_NS,
)

HTML = ElementMaker(
    namespace=XHTML_NS,
    nsmap={None: XHTML_NS, "epub": EPUB_NS},
)


@dataclass(frozen=True)
class ChapterEntry:
    id: str
    label: str
    src: str


@dataclass(frozen=True)
class VolumeEntry:
    id: str
    label: str
    src: str
    chapters: list[ChapterEntry]


@dataclass(frozen=True)
class ManifestEntry:
    id: str
    href: str
    media_type: str
    properties: str | None = None


@dataclass(frozen=True)
class SpineEntry:
    idref: str
    properties: str | None = None


@dataclass
class NavPoint:
    """
    A table-of-contents entry, possibly with nested children.
    """

    id: str
    label: str
    src: str
    children: list[NavPoint] = field(default_factory=list)

    def add_child(self, point: NavPoint) -> None:
        """
        Append a child nav point under this one.
        """
        self.children.append(point)


@dataclass
class EpubResource:
    """
    Base class for any EPUB-packaged resource.
    """

    id: str
    filename: str
    media_type: str


@dataclass
class StyleSheet(EpubResource):
    content: str
    media_type: str = field(init=False, default="text/css")


@dataclass
class ImageResource(EpubResource):
    data: bytes


@dataclass
class Chapter(EpubResource):
    title: str
    content: str
    css: list[StyleSheet] = field(default_factory=list)
    media_type: str = field(init=False, default="application/xhtml+xml")

    def __post_init__(self) -> None:
        if not self.filename:
            object.__setattr__(self, "filename", f"{self.id}.xhtml")

    def to_xhtml(self, lang: str = "zh-CN") -> str:
        """
        Generate the XHTML for a chapter.
        """
        html_el = HTML.html(
            # <head>
            HTML.head(
                # <title>
                HTML.title(self.title),
                # <link> for each stylesheet
                *[
                    HTML.link(
                        href=f"../{CSS_FOLDER}/{css.filename}",
                        rel="stylesheet",
                        type=css.media_type,
                    )
                    for css in self.css
                ],
            ),
            # <body>
            HTML.body(
                *list(html.fromstring(f'<div xmlns="{XHTML_NS}">{self.content}</div>'))
            ),
            # attributes on <html>
            lang=lang,
            **{f"{{{XML_NS}}}lang": lang},
        )
        xhtml_bytes = etree.tostring(
            html_el,
            pretty_print=PRETTY_PRINT_FLAG,
            xml_declaration=False,
            encoding="utf-8",
            method="xml",
        )
        xhtml_string: str = xhtml_bytes.decode("utf-8")
        return CHAP_DOC_TYPE + xhtml_string


@dataclass
class Volume:
    id: str
    title: str
    intro: str = ""
    cover: Path | None = None
    chapters: list[Chapter] = field(default_factory=list)

    def add_chapter(self, chapter: Chapter) -> None:
        """Append a chapter to this volume."""
        self.chapters.append(chapter)
