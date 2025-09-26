#!/usr/bin/env python3
"""
novel_downloader.libs.epub.documents
------------------------------------

Defines the classes that render EPUB navigation and packaging documents:
  * NavDocument: builds the XHTML nav.xhtml (EPUB 3)
  * NCXDocument: builds the NCX XML navigation map (EPUB 2)
  * OpfDocument: builds the content.opf package document
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import escape

from .constants import (
    NAV_TEMPLATE,
    NCX_TEMPLATE,
    OPF_TEMPLATE,
)
from .models import (
    ChapterEntry,
    EpubResource,
    ManifestEntry,
    NavPoint,
    SpineEntry,
    VolumeEntry,
)


@dataclass
class NavDocument(EpubResource):
    title: str = "未命名"
    language: str = "zh-Hans"
    id: str = "nav"
    filename: str = "nav.xhtml"
    media_type: str = field(init=False, default="application/xhtml+xml")
    content_items: list[ChapterEntry | VolumeEntry] = field(default_factory=list)

    def add_chapter(self, id: str, label: str, src: str) -> None:
        """
        Add a top-level chapter entry to the navigation.

        :param id: The unique ID for the chapter.
        :param label: The display title for the chapter.
        :param src: The href target for the chapter's XHTML file.
        """
        self.content_items.append(ChapterEntry(id=id, label=label, src=src))

    def add_volume(
        self,
        id: str,
        label: str,
        src: str,
        chapters: list[ChapterEntry],
    ) -> None:
        """
        Add a volume entry with nested chapters to the navigation.

        :param id: The unique ID for the volume.
        :param label: The display title for the volume.
        :param src: The href target for the volume's intro XHTML file.
        :param chapters: A list of chapter entries under this volume.
        """
        self.content_items.append(
            VolumeEntry(id=id, label=label, src=src, chapters=chapters)
        )

    def to_xhtml(self) -> str:
        """
        Generate the XHTML content for nav.xhtml based on the NavDocument.

        :return: A string containing the full XHTML for nav.xhtml.
        """
        items_str = self._render_items_str(self.content_items)
        raw = NAV_TEMPLATE.format(
            lang=self.language,
            id=self.id,
            title=escape(self.title, quote=False),
            items=items_str,
        )
        return raw

    @classmethod
    def _render_items_str(cls, items: Sequence[ChapterEntry | VolumeEntry]) -> str:
        lines: list[str] = []
        for item in items:
            label = escape(item.label, quote=False)
            if isinstance(item, VolumeEntry) and item.chapters:
                lines.append(f'<li><a href="{item.src}">{label}</a>')
                lines.append("  <ol>")
                child = cls._render_items_str(item.chapters)
                lines.extend(child.splitlines())
                lines.append("  </ol>")
                lines.append("</li>")
            else:
                lines.append(f'<li><a href="{item.src}">{label}</a></li>')
        return "\n".join(lines)


@dataclass
class NCXDocument(EpubResource):
    title: str = "未命名"
    uid: str = ""
    id: str = "ncx"
    filename: str = "toc.ncx"
    media_type: str = field(init=False, default="application/x-dtbncx+xml")
    nav_points: list[NavPoint] = field(default_factory=list)

    def add_chapter(
        self,
        id: str,
        label: str,
        src: str,
    ) -> None:
        """
        Add a single flat chapter entry to the NCX nav map.
        """
        self.nav_points.append(NavPoint(id=id, label=label, src=src))

    def add_volume(
        self,
        id: str,
        label: str,
        src: str,
        chapters: list[ChapterEntry],
    ) -> None:
        """
        Add a volume with nested chapters to the NCX nav map.
        """
        children = [NavPoint(id=c.id, label=c.label, src=c.src) for c in chapters]
        self.nav_points.append(NavPoint(id=id, label=label, src=src, children=children))

    def to_xml(self) -> str:
        """
        Generate the XML content for toc.ncx used in EPUB 2 navigation.

        :return: A string containing the full NCX XML document.
        """
        order = 1
        lines: list[str] = []
        for pt in self.nav_points:
            order, block = self._render_navpoint_str(pt, order)
            lines.extend(block)
        navpoints = "\n".join(lines)
        raw = NCX_TEMPLATE.format(
            uid=self.uid,
            depth=self._depth(self.nav_points),
            title=self.title,
            navpoints=navpoints,
        )
        return raw

    @classmethod
    def _depth(cls, points: list[NavPoint]) -> int:
        if not points:
            return 0
        return 1 + max(cls._depth(child.children) for child in points)

    @classmethod
    def _render_navpoint_str(cls, pt: NavPoint, order: int) -> tuple[int, list[str]]:
        lines: list[str] = []
        # open navPoint
        lines.append(f'<navPoint id="{pt.id}" playOrder="{order}">')
        order += 1
        # label and content
        label = escape(pt.label, quote=False)
        lines.append(f"<navLabel><text>{label}</text></navLabel>")
        lines.append(f'<content src="{pt.src}"/>')
        # children
        for child in pt.children:
            order, child_lines = cls._render_navpoint_str(child, order)
            lines.extend(child_lines)
        # close
        lines.append("</navPoint>")
        return order, lines


@dataclass
class OpfDocument(EpubResource):
    # metadata fields
    title: str = ""
    author: str = ""
    description: str = ""
    uid: str = ""
    subject: list[str] = field(default_factory=list)
    language: str = "zh-Hans"

    # resource identity
    id: str = "opf"
    filename: str = "content.opf"
    media_type: str = field(init=False, default="application/oebps-package+xml")

    # internal state
    include_cover: bool = False
    manifest: list[ManifestEntry] = field(default_factory=list)
    spine: list[SpineEntry] = field(default_factory=list)
    _cover_item: ManifestEntry | None = field(init=False, default=None)
    _toc_item: ManifestEntry | None = field(init=False, default=None)
    _cover_doc: ManifestEntry | None = field(init=False, default=None)

    def add_manifest_item(
        self,
        id: str,
        href: str,
        media_type: str,
        properties: str | None = None,
    ) -> None:
        entry = ManifestEntry(
            id=id,
            href=href,
            media_type=media_type,
            properties=properties,
        )
        self.manifest.append(entry)

        if properties == "cover-image":
            self._cover_item = entry
        if media_type == "application/x-dtbncx+xml":
            self._toc_item = entry
        if id == "cover":
            self._cover_doc = entry

    def add_spine_item(
        self,
        idref: str,
        properties: str | None = None,
    ) -> None:
        self.spine.append(SpineEntry(idref=idref, properties=properties))

    def set_subject(self, subject: list[str]) -> None:
        self.subject = subject

    def to_xml(self) -> str:
        """
        Generate the content.opf XML, which defines metadata, manifest, and spine.

        This function outputs a complete OPF package document that includes:
          * <metadata>: title, author, language, identifiers, etc.
          * <manifest>: all resource entries
          * <spine>: the reading order of the content
          * <guide>: optional references like cover page

        :return: A string containing the full OPF XML content.
        """
        now_iso = (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )

        # metadata block
        meta_lines: list[str] = []
        meta_lines.append(f'<meta property="dcterms:modified">{now_iso}</meta>')
        meta_lines.append(f'<dc:identifier id="id">{self.uid}</dc:identifier>')
        meta_lines.append(f"<dc:title>{escape(self.title, quote=True)}</dc:title>")
        meta_lines.append(f"<dc:language>{self.language}</dc:language>")
        if self.author:
            meta_lines.append(
                f'<dc:creator id="creator">{escape(self.author, quote=True)}</dc:creator>'  # noqa: E501
            )
            meta_lines.append(
                '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>'  # noqa: E501
            )
        if self.description:
            meta_lines.append(
                f"<dc:description>{escape(self.description, quote=True)}</dc:description>"  # noqa: E501
            )
        if self.subject:
            joined = ",".join(self.subject)
            meta_lines.append(f"<dc:subject>{escape(joined, quote=True)}</dc:subject>")
        if self.include_cover and self._cover_item:
            meta_lines.append(f'<meta name="cover" content="{self._cover_item.id}"/>')
        metadata = "\n".join(meta_lines)

        # manifest block
        man_lines: list[str] = []
        for item in self.manifest:
            props = f' properties="{item.properties}"' if item.properties else ""
            man_lines.append(
                f'<item id="{item.id}" href="{item.href}" media-type="{item.media_type}"{props}/>'  # noqa: E501
            )
        manifest_items = "\n".join(man_lines)

        # spine block
        toc_attr = f' toc="{self._toc_item.id}"' if self._toc_item else ""
        spine_lines: list[str] = []
        for ref in self.spine:
            props = f' properties="{ref.properties}"' if ref.properties else ""
            spine_lines.append(f'    <itemref idref="{ref.idref}"{props}/>')
        spine_items = "\n".join(spine_lines)

        # guide block
        if self.include_cover and self._cover_doc:
            guide_section = (
                "  <guide>\n"
                f'    <reference type="cover" title="Cover" href="{self._cover_doc.href}"/>\n'  # noqa: E501
                "  </guide>\n"
            )
        else:
            guide_section = ""

        raw = OPF_TEMPLATE.format(
            metadata=metadata,
            manifest_items=manifest_items,
            spine_toc=toc_attr,
            spine_items=spine_items,
            guide_section=guide_section,
        )
        return raw
