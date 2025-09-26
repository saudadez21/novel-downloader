#!/usr/bin/env python3
"""
novel_downloader.libs.epub.models
---------------------------------

Defines the core EPUB data models and resource classes used by the builder:
  * Typed entries for table of contents (ChapterEntry, VolumeEntry)
  * Manifest and spine record types (ManifestEntry, SpineEntry)
  * Hierarchical NavPoint for NCX navigation
  * Base resource class (EpubResource) and specializations:
    * StyleSheet
    * ImageResource
    * Chapter (with XHTML serialization)
  * Volume container for grouping chapters with optional intro and cover
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .constants import (
    CHAP_TMPLATE,
    CSS_TMPLATE,
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

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        """
        Generate the XHTML for a chapter.
        """
        links = "\n".join(
            CSS_TMPLATE.format(filename=css.filename, media_type=css.media_type)
            for css in self.css
        )
        return CHAP_TMPLATE.format(
            lang=lang,
            title=self.title,
            xlinks=links,
            content=self.content,
        )


@dataclass
class Volume:
    id: str
    title: str
    intro: str = ""
    cover: Path | None = None
    chapters: list[Chapter] = field(default_factory=list)
