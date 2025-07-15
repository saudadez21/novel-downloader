#!/usr/bin/env python3
"""
novel_downloader.utils.epub.documents
-------------------------------------

Defines the classes that render EPUB navigation and packaging documents:
- NavDocument: builds the XHTML nav.xhtml (EPUB 3)
- NCXDocument: builds the NCX XML navigation map (EPUB 2)
- OpfDocument: builds the content.opf package document
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from lxml import etree
from lxml.builder import ElementMaker

from .constants import (
    DC_NS,
    EPUB_NS,
    NCX_NS,
    OPF_NS,
    OPF_PKG_ATTRIB,
    PRETTY_PRINT_FLAG,
    XHTML_NS,
    XML_NS,
)
from .models import (
    ChapterEntry,
    EpubResource,
    ManifestEntry,
    NavPoint,
    SpineEntry,
    VolumeEntry,
)

NAV = ElementMaker(
    namespace=XHTML_NS,
    nsmap={None: XHTML_NS, "epub": EPUB_NS},
)
NCX = ElementMaker(namespace=NCX_NS, nsmap={None: NCX_NS})
PKG = ElementMaker(
    namespace=OPF_NS,
    nsmap={
        None: OPF_NS,
        "dc": DC_NS,
        "opf": OPF_NS,
    },
)
DC = ElementMaker(namespace=DC_NS)


@dataclass
class NavDocument(EpubResource):
    title: str = "未命名"
    language: str = "zh-CN"
    id: str = "nav"
    filename: str = "nav.xhtml"
    media_type: str = field(init=False, default="application/xhtml+xml")
    content_items: list[ChapterEntry | VolumeEntry] = field(default_factory=list)

    def add_chapter(
        self,
        id: str,
        label: str,
        src: str,
    ) -> None:
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
        # build the root <html> with both lang attributes
        html_el = NAV.html(
            # head/title
            NAV.head(NAV.title(self.title)),
            # body/nav/ol subtree
            NAV.body(
                NAV.nav(
                    NAV.h2(self.title),
                    NAV.ol(*self._render_items(self.content_items)),
                    # namespaced + regular attributes
                    **{
                        f"{{{EPUB_NS}}}type": "toc",
                        "id": self.id,
                        "role": "doc-toc",
                    },
                )
            ),
            # html attributes
            lang=self.language,
            **{f"{{{XML_NS}}}lang": self.language},
        )

        xml_bytes = etree.tostring(
            html_el,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=PRETTY_PRINT_FLAG,
            doctype="<!DOCTYPE html>",
        )
        xml_string: str = xml_bytes.decode("utf-8")
        return xml_string

    @classmethod
    def _render_items(
        cls,
        items: Sequence[ChapterEntry | VolumeEntry],
    ) -> list[etree._Element]:
        """
        Recursively build <li> elements (and nested <ol>) for each TOC entry.
        """
        elements: list[etree._Element] = []
        for item in items:
            if isinstance(item, VolumeEntry) and item.chapters:
                li = NAV.li(NAV.a(item.label, href=item.src))
                li.append(NAV.ol(*cls._render_items(item.chapters)))
            else:
                li = NAV.li(NAV.a(item.label, href=item.src))
            elements.append(li)
        return elements


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
        root = NCX.ncx(version="2005-1")
        head = NCX.head(
            NCX.meta(name="dtb:uid", content=self.uid),
            NCX.meta(name="dtb:depth", content=str(self._depth(self.nav_points))),
            NCX.meta(name="dtb:totalPageCount", content="0"),
            NCX.meta(name="dtb:maxPageNumber", content="0"),
        )
        root.append(head)
        root.append(NCX.docTitle(NCX.text(self.title)))

        navMap = NCX.navMap()
        root.append(navMap)

        self._render_navpoints(navMap, self.nav_points, start=1)

        xml_bytes = etree.tostring(
            root,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=PRETTY_PRINT_FLAG,
        )
        xml_string: str = xml_bytes.decode("utf-8")
        return xml_string

    @classmethod
    def _depth(cls, points: list[NavPoint]) -> int:
        if not points:
            return 0
        return 1 + max(cls._depth(child.children) for child in points)

    @classmethod
    def _render_navpoints(
        cls,
        parent: etree._Element,
        points: list[NavPoint],
        start: int,
    ) -> int:
        """
        Recursively append <navPoint> elements under `parent`,
        assigning playOrder starting from `start`.
        Returns the next unused playOrder.
        """
        play = start
        for pt in points:
            np = etree.SubElement(
                parent,
                "navPoint",
                id=pt.id,
                playOrder=str(play),
            )
            play += 1
            navLabel = etree.SubElement(np, "navLabel")
            lbl_text = etree.SubElement(navLabel, "text")
            lbl_text.text = pt.label
            etree.SubElement(np, "content", src=pt.src)
            play = cls._render_navpoints(np, pt.children, play)
        return play


@dataclass
class OpfDocument(EpubResource):
    # metadata fields
    title: str = ""
    author: str = ""
    description: str = ""
    uid: str = ""
    subject: list[str] = field(default_factory=list)
    language: str = "zh-CN"

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
        - <metadata>: title, author, language, identifiers, etc.
        - <manifest>: all resource entries
        - <spine>: the reading order of the content
        - <guide>: optional references like cover page

        :return: A string containing the full OPF XML content.
        """
        now_iso = datetime.now(UTC).replace(microsecond=0).isoformat()

        # <package> root
        package = PKG.package(**OPF_PKG_ATTRIB)

        # <metadata>
        metadata = PKG.metadata()
        package.append(metadata)

        # modified timestamp
        modified = PKG.meta(property="dcterms:modified")
        modified.text = now_iso
        metadata.append(modified)

        # mandatory DC elements
        id_el = DC.identifier(id="id")
        id_el.text = self.uid
        title_el = DC.title()
        title_el.text = self.title
        lang_el = DC.language()
        lang_el.text = self.language
        metadata.extend([id_el, title_el, lang_el])

        # optional DC elements
        if self.author:
            creator = DC.creator(id="creator")
            creator.text = self.author
            metadata.append(creator)
        if self.description:
            desc = DC.description()
            desc.text = self.description
            metadata.append(desc)
        if self.subject:
            subj = DC.subject()
            subj.text = ",".join(self.subject)
            metadata.append(subj)
        if self.include_cover and self._cover_item:
            cover_meta = PKG.meta(name="cover", content=self._cover_item.id)
            metadata.append(cover_meta)

        # <manifest>
        manifest_el = PKG.manifest()
        for item in self.manifest:
            attrs = {
                "id": item.id,
                "href": item.href,
                "media-type": item.media_type,
            }
            if item.properties:
                attrs["properties"] = item.properties
            manifest_el.append(PKG.item(**attrs))
        package.append(manifest_el)

        # <spine>
        spine_attrs = {}
        if self._toc_item:
            spine_attrs["toc"] = self._toc_item.id
        spine_el = PKG.spine(**spine_attrs)
        for ref in self.spine:
            attrs = {"idref": ref.idref}
            if ref.properties:
                attrs["properties"] = ref.properties
            spine_el.append(PKG.itemref(**attrs))
        package.append(spine_el)

        # optional <guide> for cover
        if self.include_cover and self._cover_doc:
            guide_el = PKG.guide()
            guide_el.append(
                PKG.reference(
                    type="cover",
                    title="Cover",
                    href=self._cover_doc.href,
                )
            )
            package.append(guide_el)

        xml_bytes = etree.tostring(
            package,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=PRETTY_PRINT_FLAG,
        )
        xml_string: str = xml_bytes.decode("utf-8")
        return xml_string
