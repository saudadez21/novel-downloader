#!/usr/bin/env python3
"""
novel_downloader.core.exporters.epub_builder
--------------------------------------------

Provides classes and utilities to assemble novel content
into a standards-compliant EPUB file.

Key components:

- EpubBuilder : orchestrates metadata, manifest, spine, navigation, and resources
- EpubResource : base for items like StyleSheet, ImageResource
- NavDocument/NCX : generate EPUB3 XHTML nav and EPUB2 NCX tables of contents
- OpfDocument : builds the EPUB package (.opf) with metadata, manifest, spine, guide
- Chapter, Volume : represent and render content sections and volume intros

Usage example:

```python
builder = EpubBuilder(title="My Novel", author="Author Name", uid="uuid-1234")
builder.add_chapter(Chapter(id="ch1", title="Chapter 1", content="<p>xxx</p>"))
builder.export("output/my_novel.epub")
```
"""

import hashlib
import zipfile
from collections.abc import Sequence
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import NotRequired, Self, TypedDict
from zipfile import ZIP_DEFLATED, ZIP_STORED

from lxml import etree, html
from lxml.etree import _Element

from novel_downloader.utils.constants import (
    CSS_VOLUME_INTRO_PATH,
    VOLUME_BORDER_IMAGE_PATH,
)

_ROOT_PATH = "OEBPS"
_IMAGE_FOLDER = "Images"
_TEXT_FOLDER = "Text"
_CSS_FOLDER = "Styles"

_IMAGE_MEDIA_TYPES: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}

_CONTAINER_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="{root_path}/content.opf"
            media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""

_COVER_IMAGE_TEMPLATE = (
    f'<div style="text-align: center; margin: 0; padding: 0;">'
    f'<img src="../{_IMAGE_FOLDER}/cover.{{ext}}" alt="cover" '
    f'style="max-width: 100%; height: auto;" />'
    f"</div>"
)


class ChapterEntry(TypedDict):
    id: str
    label: str
    src: str
    chapters: NotRequired[list["ChapterEntry"]]


class VolumeEntry(TypedDict):
    id: str
    label: str
    src: str
    chapters: list[ChapterEntry]


class ManifestEntry(TypedDict):
    id: str
    href: str
    media_type: str
    properties: str | None


class SpineEntry(TypedDict):
    idref: str
    properties: str | None


class NavPoint:
    def __init__(
        self,
        id: str,
        label: str,
        src: str,
        children: list[Self] | None = None,
    ):
        self._id = id
        self._label = label
        self._src = src
        self._children = children or []

    def add_child(self, point: Self) -> None:
        """
        Append a child nav point under this one.
        """
        self._children.append(point)

    @property
    def id(self) -> str:
        """
        Unique identifier for this navigation point.
        """
        return self._id

    @property
    def label(self) -> str:
        """
        Display text shown in the TOC for this point.
        """
        return self._label

    @property
    def src(self) -> str:
        """
        Path to the target content file (e.g., chapter XHTML).
        """
        return self._src

    @property
    def children(self) -> list[Self]:
        """
        Nested navigation points under this one, if any.
        """
        return self._children


class EpubResource:
    def __init__(
        self,
        id: str,
        filename: str,
        media_type: str,
    ):
        self._id = id
        self._filename = filename
        self._media_type = media_type

    @property
    def id(self) -> str:
        return self._id

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def media_type(self) -> str:
        return self._media_type


class StyleSheet(EpubResource):
    def __init__(
        self,
        id: str,
        content: str,
        filename: str = "style.css",
    ):
        super().__init__(
            id=id,
            filename=filename,
            media_type="text/css",
        )
        self._content = content

    @property
    def content(self) -> str:
        return self._content


class ImageResource(EpubResource):
    def __init__(
        self,
        id: str,
        data: bytes,
        media_type: str,
        filename: str,
    ):
        super().__init__(
            id=id,
            filename=filename,
            media_type=media_type,
        )
        self._data = data

    @property
    def data(self) -> bytes:
        return self._data


class NavDocument(EpubResource):
    def __init__(
        self,
        title: str = "未命名",
        language: str = "zh-CN",
        id: str = "nav",
        filename: str = "nav.xhtml",
    ):
        super().__init__(
            id=id,
            filename=filename,
            media_type="application/xhtml+xml",
        )
        self._title = title
        self._language = language
        self._content_items: list[ChapterEntry | VolumeEntry] = []

    def add_chapter(
        self,
        id: str,
        label: str,
        src: str,
    ) -> None:
        """
        Add a top-level chapter entry to the navigation structure.

        :param id: The unique ID for the chapter.
        :param label: The display title for the chapter.
        :param src: The href target for the chapter's XHTML file.
        """
        self._content_items.append(
            {
                "id": id,
                "label": label,
                "src": src,
            }
        )

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
        self._content_items.append(
            {
                "id": id,
                "label": label,
                "src": src,
                "chapters": chapters,
            }
        )

    @property
    def title(self) -> str:
        return self._title

    @property
    def language(self) -> str:
        return self._language

    @property
    def content_items(self) -> list[ChapterEntry | VolumeEntry]:
        return self._content_items

    def to_xhtml(self) -> str:
        """
        Generate the XHTML content for nav.xhtml based on the NavDocument.

        :param nav: A NavDocument instance containing navigation data.
        :return: A string containing the full XHTML for nav.xhtml.
        """
        XHTML_NS = "http://www.w3.org/1999/xhtml"
        EPUB_NS = "http://www.idpf.org/2007/ops"
        XML_NS = "http://www.w3.org/XML/1998/namespace"

        nsmap_root = {
            None: XHTML_NS,
            "epub": EPUB_NS,
        }

        html = etree.Element(
            f"{{{XHTML_NS}}}html",
            nsmap=nsmap_root,
            lang=self.language,
        )
        # xml:lang
        html.set(f"{{{XML_NS}}}lang", self.language)

        # <head><title>
        head = etree.SubElement(html, f"{{{XHTML_NS}}}head")
        title_el = etree.SubElement(head, f"{{{XHTML_NS}}}title")
        title_el.text = self.title

        # <body><nav epub:type="toc" id="..." role="doc-toc">
        body = etree.SubElement(html, f"{{{XHTML_NS}}}body")
        nav_el = etree.SubElement(
            body,
            f"{{{XHTML_NS}}}nav",
            {
                f"{{{EPUB_NS}}}type": "toc",
                "id": self.id,
                "role": "doc-toc",
            },
        )

        h2 = etree.SubElement(nav_el, f"{{{XHTML_NS}}}h2")
        h2.text = self.title

        # <ol> ... </ol>
        def _add_items(
            parent_ol: _Element,
            items: Sequence[ChapterEntry | VolumeEntry],
        ) -> None:
            for item in items:
                li = etree.SubElement(parent_ol, f"{{{XHTML_NS}}}li")
                a = etree.SubElement(li, f"{{{XHTML_NS}}}a", href=item["src"])
                a.text = item["label"]
                if "chapters" in item and item["chapters"]:
                    sub_ol = etree.SubElement(li, f"{{{XHTML_NS}}}ol")
                    _add_items(sub_ol, item["chapters"])

        top_ol = etree.SubElement(nav_el, f"{{{XHTML_NS}}}ol")
        _add_items(top_ol, self.content_items)

        xml_bytes: bytes = etree.tostring(
            html,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=True,
            doctype="<!DOCTYPE html>",
        )
        return xml_bytes.decode("utf-8")


class NCXDocument(EpubResource):
    def __init__(
        self,
        title: str = "未命名",
        uid: str = "",
        id: str = "ncx",
        filename: str = "toc.ncx",
    ):
        super().__init__(
            id=id,
            filename=filename,
            media_type="application/x-dtbncx+xml",
        )
        self._title = title
        self._uid = uid
        self._nav_points: list[NavPoint] = []

    def add_chapter(
        self,
        id: str,
        label: str,
        src: str,
    ) -> None:
        """
        Add a single flat chapter entry to the NCX nav map.
        """
        self._nav_points.append(NavPoint(id=id, label=label, src=src))

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
        children = [
            NavPoint(id=c["id"], label=c["label"], src=c["src"]) for c in chapters
        ]
        self._nav_points.append(
            NavPoint(id=id, label=label, src=src, children=children)
        )

    @property
    def nav_points(self) -> list[NavPoint]:
        return self._nav_points

    @property
    def title(self) -> str:
        return self._title

    @property
    def uid(self) -> str:
        return self._uid

    def to_xml(self) -> str:
        """
        Generate the XML content for toc.ncx used in EPUB 2 navigation.

        :param ncx: An NCXDocument instance representing the table of contents.
        :return: A string containing the full NCX XML document.
        """
        nsmap_root = {None: "http://www.daisy.org/z3986/2005/ncx/"}
        root = etree.Element("ncx", nsmap=nsmap_root, version="2005-1")

        # head
        head = etree.SubElement(root, "head")
        etree.SubElement(head, "meta", name="dtb:uid", content=self.uid)

        def _depth(points: list[NavPoint]) -> int:
            if not points:
                return 0
            return 1 + max(_depth(p.children) for p in points)

        depth = _depth(self.nav_points)
        etree.SubElement(head, "meta", name="dtb:depth", content=str(depth))
        etree.SubElement(head, "meta", name="dtb:totalPageCount", content="0")
        etree.SubElement(head, "meta", name="dtb:maxPageNumber", content="0")

        # docTitle
        docTitle = etree.SubElement(root, "docTitle")
        text = etree.SubElement(docTitle, "text")
        text.text = self.title

        # navMap
        navMap = etree.SubElement(root, "navMap")
        play_order = 1

        def _add_navpoint(point: NavPoint, parent: _Element) -> None:
            nonlocal play_order
            np = etree.SubElement(
                parent,
                "navPoint",
                id=point.id,
                playOrder=str(play_order),
            )
            play_order += 1

            navLabel = etree.SubElement(np, "navLabel")
            lbl_text = etree.SubElement(navLabel, "text")
            lbl_text.text = point.label

            etree.SubElement(np, "content", src=point.src)

            for child in point.children:
                _add_navpoint(child, np)

        for pt in self.nav_points:
            _add_navpoint(pt, navMap)

        xml_bytes: bytes = etree.tostring(
            root,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=True,
        )
        return xml_bytes.decode("utf-8")


class OpfDocument(EpubResource):
    def __init__(
        self,
        title: str,
        author: str = "",
        description: str = "",
        uid: str = "",
        subject: list[str] | None = None,
        language: str = "zh-CN",
        id: str = "opf",
        filename: str = "content.opf",
    ):
        super().__init__(
            id=id,
            filename=filename,
            media_type="application/oebps-package+xml",
        )
        self._title = title
        self._author = author
        self._description = description
        self._uid = uid
        self._language = language
        self._include_cover = False
        self._subject: list[str] = subject or []
        self._manifest: list[ManifestEntry] = []
        self._spine: list[SpineEntry] = []

    def add_manifest_item(
        self,
        id: str,
        href: str,
        media_type: str,
        properties: str | None = None,
    ) -> None:
        self._manifest.append(
            {
                "id": id,
                "href": href,
                "media_type": media_type,
                "properties": properties,
            }
        )

    def add_spine_item(
        self,
        idref: str,
        properties: str | None = None,
    ) -> None:
        self._spine.append({"idref": idref, "properties": properties})

    def set_subject(self, subject: list[str]) -> None:
        self._subject = subject

    @property
    def title(self) -> str:
        """
        Book title metadata.
        """
        return self._title

    @property
    def author(self) -> str:
        """
        Author metadata.
        """
        return self._author

    @property
    def description(self) -> str:
        """
        Book description metadata.
        """
        return self._description

    @property
    def subject(self) -> list[str]:
        return self._subject

    @property
    def uid(self) -> str:
        """
        Unique identifier for the book, used in dc:identifier and NCX UID.
        """
        return self._uid

    @property
    def language(self) -> str:
        return self._language

    @property
    def include_cover(self) -> bool:
        """
        Whether to include a cover item in the <guide> section.
        """
        return self._include_cover

    @include_cover.setter
    def include_cover(self, value: bool) -> None:
        self._include_cover = value

    @property
    def manifest(self) -> list[ManifestEntry]:
        """
        All resources used by the book (XHTML, CSS, images, nav, etc.).
        """
        return self._manifest

    @property
    def spine(self) -> list[SpineEntry]:
        """
        Defines the reading order of the book's contents.
        """
        return self._spine

    def to_xml(self) -> str:
        """
        Generate the content.opf XML, which defines metadata, manifest, and spine.

        This function outputs a complete OPF package document that includes:
        - <metadata>: title, author, language, identifiers, etc.
        - <manifest>: all resource entries
        - <spine>: the reading order of the content
        - <guide>: optional references like cover page

        :param opf: An OpfDocument instance with metadata and content listings.
        :return: A string containing the full OPF XML content.
        """
        OPF_NS = "http://www.idpf.org/2007/opf"
        DC_NS = "http://purl.org/dc/elements/1.1/"
        # package root
        nsmap_root = {None: OPF_NS}
        meta_nsmap = {
            "dc": DC_NS,
            "opf": OPF_NS,
        }

        # <package>
        pkg_attrib = {
            "version": "3.0",
            "unique-identifier": "id",
            "prefix": "rendition: http://www.idpf.org/vocab/rendition/#",
        }
        package = etree.Element(
            f"{{{OPF_NS}}}package", attrib=pkg_attrib, nsmap=nsmap_root
        )

        # <metadata>
        metadata = etree.SubElement(package, f"{{{OPF_NS}}}metadata", nsmap=meta_nsmap)

        now = datetime.now(UTC).replace(microsecond=0).isoformat()
        m = etree.SubElement(
            metadata,
            f"{{{OPF_NS}}}meta",
            attrib={"property": "dcterms:modified"},
        )
        m.text = now

        dc_id = etree.SubElement(
            metadata,
            f"{{{DC_NS}}}identifier",
            id="id",
        )
        dc_id.text = self.uid

        dc_title = etree.SubElement(
            metadata,
            f"{{{DC_NS}}}title",
        )
        dc_title.text = self.title

        dc_lang = etree.SubElement(
            metadata,
            f"{{{DC_NS}}}language",
        )
        dc_lang.text = self.language

        if self.author:
            dc_creator = etree.SubElement(
                metadata,
                f"{{{DC_NS}}}creator",
                id="creator",
            )
            dc_creator.text = self.author

        if self.description:
            dc_desc = etree.SubElement(
                metadata,
                f"{{{DC_NS}}}description",
            )
            dc_desc.text = self.description

        if self.subject:
            subj_text = ",".join(self.subject)
            dc_subject = etree.SubElement(
                metadata,
                f"{{{DC_NS}}}subject",
            )
            dc_subject.text = subj_text

        if self.include_cover:
            cover = next(
                (m for m in self.manifest if m["properties"] == "cover-image"),
                None,
            )
            if cover:
                etree.SubElement(
                    metadata,
                    f"{{{OPF_NS}}}meta",
                    name="cover",
                    content=cover["id"],
                )

        # <manifest>
        manifest = etree.SubElement(package, f"{{{OPF_NS}}}manifest")
        for item in self.manifest:
            attrs = {
                "href": item["href"],
                "id": item["id"],
                "media-type": item["media_type"],
            }
            if item["properties"]:
                attrs["properties"] = item["properties"]
            etree.SubElement(manifest, f"{{{OPF_NS}}}item", attrib=attrs)

        spine_attrs = {}
        toc_item = next(
            (m for m in self.manifest if m["media_type"] == "application/x-dtbncx+xml"),
            None,
        )
        if toc_item:
            spine_attrs["toc"] = toc_item["id"]
        spine = etree.SubElement(package, f"{{{OPF_NS}}}spine", **spine_attrs)
        for ref in self.spine:
            attrs = {"idref": ref["idref"]}
            if ref["properties"]:
                attrs["properties"] = ref["properties"]
            etree.SubElement(spine, f"{{{OPF_NS}}}itemref", attrib=attrs)

        # <guide>
        if self.include_cover:
            cover_ref = next((m for m in self.manifest if m["id"] == "cover"), None)
            if cover_ref:
                guide = etree.SubElement(package, f"{{{OPF_NS}}}guide")
                etree.SubElement(
                    guide,
                    f"{{{OPF_NS}}}reference",
                    type="cover",
                    title="Cover",
                    href=cover_ref["href"],
                )

        xml_bytes: bytes = etree.tostring(
            package,
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=True,
        )
        return xml_bytes.decode("utf-8")


class Chapter(EpubResource):
    def __init__(
        self,
        id: str,
        title: str,
        content: str,
        css: list[StyleSheet] | None = None,
        filename: str | None = None,
    ):
        filename = filename or f"{id}.xhtml"
        super().__init__(
            id=id,
            filename=filename,
            media_type="application/xhtml+xml",
        )
        self._title = title
        self._content = content
        self._css = css or []

    @property
    def title(self) -> str:
        return self._title

    def to_xhtml(self, lang: str = "zh-CN") -> str:
        # Prepare namespace map
        NSMAP = {
            None: "http://www.w3.org/1999/xhtml",
            "epub": "http://www.idpf.org/2007/ops",
        }
        # Create <html> root with xml:lang and lang
        html_el = etree.Element(
            "{http://www.w3.org/1999/xhtml}html",
            nsmap=NSMAP,
            attrib={
                "{http://www.w3.org/XML/1998/namespace}lang": lang,
                "lang": lang,
            },
        )

        # Build <head>
        head = etree.SubElement(html_el, "head")
        title = etree.SubElement(head, "title")
        title.text = self._title

        # Add stylesheet links
        for css in self._css:
            etree.SubElement(
                head,
                "link",
                attrib={
                    "href": f"../{_CSS_FOLDER}/{css.filename}",
                    "rel": "stylesheet",
                    "type": css.media_type,
                },
            )

        # Build <body>
        body = etree.SubElement(html_el, "body")
        wrapper = html.fromstring(
            f'<div xmlns="http://www.w3.org/1999/xhtml">{self._content}</div>'
        )
        for node in wrapper:
            body.append(node)

        xhtml_bytes: bytes = etree.tostring(
            html_el,
            pretty_print=True,
            xml_declaration=False,  # we'll do it ourselves
            encoding="utf-8",
            method="xml",
        )
        doctype = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<!DOCTYPE html PUBLIC "
            '"-//W3C//DTD XHTML 1.1//EN" '
            '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
        )
        return doctype + xhtml_bytes.decode("utf-8")


class Volume:
    def __init__(
        self,
        id: str,
        title: str,
        intro: str = "",
        cover: Path | None = None,
        chapters: list[Chapter] | None = None,
    ):
        self._id = id
        self._title = title
        self._intro = intro
        self._cover = cover
        self._chapters = chapters or []

    def add_chapter(self, chapter: Chapter) -> None:
        """
        Append a chapter to this volume.
        """
        self._chapters.append(chapter)

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def intro(self) -> str:
        """
        Optional volume description or introduction text.
        """
        return self._intro

    @property
    def cover(self) -> Path | None:
        """
        Optional volume-specific cover image.
        """
        return self._cover

    @property
    def chapters(self) -> list[Chapter]:
        return self._chapters


class EpubBuilder:
    def __init__(
        self,
        title: str,
        author: str = "",
        description: str = "",
        cover_path: Path | None = None,
        subject: list[str] | None = None,
        serial_status: str = "",
        word_count: str = "0",
        uid: str = "",
        language: str = "zh-CN",
    ):
        self._title = title
        self._author = author
        self._description = description
        self._language = language

        self._subject: list[str] = subject or []
        self._serial_status = serial_status
        self._word_count = word_count

        self._content_items: list[Chapter] = []
        self._images: list[ImageResource] = []
        self._img_map: dict[str, str] = {}
        self._stylesheets: list[StyleSheet] = []
        self._img_idx = 0
        self._vol_idx = 0

        self._nav = NavDocument(title=title, language=language)
        self._ncx = NCXDocument(title=title, uid=uid)
        self._opf = OpfDocument(
            title=title,
            author=author,
            description=description,
            uid=uid,
            subject=subject,
            language=language,
        )
        self._opf.add_manifest_item(
            id="ncx",
            href="toc.ncx",
            media_type="application/x-dtbncx+xml",
        )
        self._opf.add_manifest_item(
            id="nav",
            href="nav.xhtml",
            media_type="application/xhtml+xml",
            properties="nav",
        )

        self._vol_intro_css = StyleSheet(
            id="volume_style",
            content=CSS_VOLUME_INTRO_PATH.read_text(encoding="utf-8"),
            filename="volume_style.css",
        )
        with suppress(FileNotFoundError):
            self._images.append(
                ImageResource(
                    id="img-volume-border",
                    data=VOLUME_BORDER_IMAGE_PATH.read_bytes(),
                    media_type="image/png",
                    filename="volume_border.png",
                )
            )
        self._opf.add_manifest_item(
            id="img-volume-border",
            href=f"{_IMAGE_FOLDER}/volume_border.png",
            media_type="image/png",
        )
        self._opf.add_manifest_item(
            id="volume_style",
            href=f"{_CSS_FOLDER}/volume_style.css",
            media_type="text/css",
        )
        self._stylesheets.append(self._vol_intro_css)

        if cover_path and cover_path.exists() and cover_path.is_file():
            ext = cover_path.suffix.lower().lstrip(".")
            media_type = _IMAGE_MEDIA_TYPES.get(ext)
            if media_type:
                data = cover_path.read_bytes()

                # create the CoverImage
                self._images.append(
                    ImageResource(
                        id="cover-img",
                        data=data,
                        media_type=media_type,
                        filename=f"cover.{ext}",
                    )
                )
                self._content_items.append(
                    Chapter(
                        id="cover",
                        title="Cover",
                        content=_COVER_IMAGE_TEMPLATE.format(ext=ext),
                        filename="cover.xhtml",
                    )
                )

                self._opf.add_manifest_item(
                    id="cover-img",
                    href=f"{_IMAGE_FOLDER}/cover.{ext}",
                    media_type=media_type,
                    properties="cover-image",
                )

                self._opf.add_manifest_item(
                    id="cover",
                    href=f"{_TEXT_FOLDER}/cover.xhtml",
                    media_type="application/xhtml+xml",
                )
                self._opf.add_spine_item(
                    idref="cover",
                    properties="duokan-page-fullscreen",
                )

                self._opf.include_cover = True

        # intro
        intro_html = self._gen_book_intro(
            book_name=title,
            author=author,
            serial_status=serial_status,
            subject=self._subject,
            word_count=word_count,
            summary=description,
        )
        self._content_items.append(
            Chapter(
                id="intro",
                title="书籍简介",
                content=intro_html,
                filename="intro.xhtml",
            )
        )
        self._opf.add_manifest_item(
            id="intro",
            href=f"{_TEXT_FOLDER}/intro.xhtml",
            media_type="application/xhtml+xml",
        )
        self._opf.add_spine_item(
            idref="intro",
        )
        self._nav.add_chapter(
            id="intro",
            label="书籍简介",
            src=f"{_TEXT_FOLDER}/intro.xhtml",
        )
        self._ncx.add_chapter(
            id="intro",
            label="书籍简介",
            src=f"{_TEXT_FOLDER}/intro.xhtml",
        )

    def export(self, output_path: str | Path) -> Path | None:
        """
        Build and export the current book as an EPUB file.

        :param output_path: Path to save the final .epub file.
        """
        return self._build_epub(
            output_path=Path(output_path),
        )

    @property
    def content_items(self) -> list[Chapter]:
        """
        Ordered list of contents.
        """
        return self._content_items

    @property
    def images(self) -> list[ImageResource]:
        return self._images

    @property
    def stylesheets(self) -> list[StyleSheet]:
        return self._stylesheets

    @property
    def nav(self) -> NavDocument:
        return self._nav

    @property
    def ncx(self) -> NCXDocument:
        return self._ncx

    @property
    def opf(self) -> OpfDocument:
        return self._opf

    def add_chapter(self, chapter: Chapter) -> None:
        self._ncx.add_chapter(
            id=chapter.id,
            label=chapter.title,
            src=f"{_TEXT_FOLDER}/{chapter.filename}",
        )
        self._nav.add_chapter(
            id=chapter.id,
            label=chapter.title,
            src=f"{_TEXT_FOLDER}/{chapter.filename}",
        )
        self._opf.add_manifest_item(
            id=chapter.id,
            href=f"{_TEXT_FOLDER}/{chapter.filename}",
            media_type=chapter.media_type,
        )
        self._opf.add_spine_item(idref=chapter.id)

        self._content_items.append(chapter)

    def add_volume(self, volume: Volume) -> None:
        if volume.cover:
            cover_path = self.add_image(volume.cover)
            cover = f'<img class="width100" src="../{_IMAGE_FOLDER}/{cover_path}"/>'
            self._content_items.append(
                Chapter(
                    id=f"vol_{self._vol_idx}_cover",
                    title=volume.title,
                    content=cover,
                    filename=f"vol_{self._vol_idx}_cover.xhtml",
                )
            )
            self._opf.add_manifest_item(
                id=f"vol_{self._vol_idx}_cover",
                href=f"{_TEXT_FOLDER}/vol_{self._vol_idx}_cover.xhtml",
                media_type="application/xhtml+xml",
            )
            self._opf.add_spine_item(
                idref=f"vol_{self._vol_idx}_cover",
                properties="duokan-page-fullscreen",
            )

        self._content_items.append(
            Chapter(
                id=f"vol_{self._vol_idx}",
                title=volume.title,
                content=self._create_volume_intro(volume.title, volume.intro),
                filename=f"vol_{self._vol_idx}.xhtml",
                css=[self._vol_intro_css],
            )
        )
        self._opf.add_manifest_item(
            id=f"vol_{self._vol_idx}",
            href=f"{_TEXT_FOLDER}/vol_{self._vol_idx}.xhtml",
            media_type="application/xhtml+xml",
        )
        self._opf.add_spine_item(
            idref=f"vol_{self._vol_idx}",
        )
        vol_chapters: list[ChapterEntry] = []
        for chap in volume.chapters:
            chap_id = chap.id
            chap_label = chap.title
            chap_src = f"{_TEXT_FOLDER}/{chap.filename}"
            vol_chapters.append(
                {
                    "id": chap_id,
                    "label": chap_label,
                    "src": chap_src,
                }
            )
            self._opf.add_manifest_item(
                id=chap_id,
                href=chap_src,
                media_type=chap.media_type,
            )
            self._opf.add_spine_item(
                idref=chap_id,
            )
        self._ncx.add_volume(
            id=f"vol_{self._vol_idx}",
            label=volume.title,
            src=f"{_TEXT_FOLDER}/vol_{self._vol_idx}.xhtml",
            chapters=vol_chapters,
        )
        self._nav.add_volume(
            id=f"vol_{self._vol_idx}",
            label=volume.title,
            src=f"{_TEXT_FOLDER}/vol_{self._vol_idx}.xhtml",
            chapters=vol_chapters,
        )
        self._content_items.extend(volume.chapters)
        self._vol_idx += 1

    def add_image(self, image_path: Path) -> str:
        if not image_path.exists() or not image_path.is_file():
            return ""
        image_hash = self._hash_file(image_path)
        if image_hash in self._img_map:
            return self._img_map[image_hash]

        ext = image_path.suffix.lower().lstrip(".")
        media_type = _IMAGE_MEDIA_TYPES.get(ext)
        if media_type is None:
            return ""

        resource_id = f"img_{self._img_idx}"
        filename = f"{resource_id}.{ext}"
        data = image_path.read_bytes()
        href = f"{_IMAGE_FOLDER}/{filename}"
        self._img_map[image_hash] = filename

        img_res = ImageResource(
            id=resource_id,
            data=data,
            media_type=media_type,
            filename=filename,
        )
        self._images.append(img_res)

        self._opf.add_manifest_item(
            id=resource_id,
            href=href,
            media_type=media_type,
        )
        self._img_idx += 1

        return filename

    def add_stylesheet(self, css: StyleSheet) -> None:
        self._stylesheets.append(css)
        self._opf.add_manifest_item(
            id=css.id,
            href=f"{_CSS_FOLDER}/{css.filename}",
            media_type=css.media_type,
        )

    @staticmethod
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

    @classmethod
    def _create_volume_intro(
        cls,
        volume_title: str,
        volume_intro_text: str = "",
    ) -> str:
        """
        Generate the HTML snippet for a volume's introduction section.

        :param volume_title: Title of the volume.
        :param volume_intro_text: Optional introduction text for the volume.
        :return: HTML string representing the volume's intro section.
        """
        line1, line2 = cls._split_volume_title(volume_title)

        def _make_border_img(class_name: str) -> str:
            return (
                f'<div class="{class_name}">'
                f'<img alt="" class="{class_name}" '
                f'src="../{_IMAGE_FOLDER}/volume_border.png" />'
                f"</div>"
            )

        html_parts = [_make_border_img("border1")]
        html_parts.append(f'<h1 class="volume-title-line1">{line1}</h1>')
        html_parts.append(_make_border_img("border2"))
        if line2:
            html_parts.append(f'<p class="volume-title-line2">{line2}</p>')

        if volume_intro_text:
            lines = [
                line.strip() for line in volume_intro_text.split("\n") if line.strip()
            ]
            html_parts.extend(f'<p class="intro">{line}</p>' for line in lines)

        return "\n".join(html_parts)

    @staticmethod
    def _gen_book_intro(
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
        # Start composing the HTML output
        html_parts = ["<h1>书籍简介</h1>", '<div class="list">', "<ul>"]

        if book_name:
            html_parts.append(f"<li>书名: 《{book_name}》</li>")
        if author:
            html_parts.append(f"<li>作者: {author}</li>")
        if subject:
            subject_str = ", ".join(subject)
            html_parts.append(f"<li>分类: {subject_str}</li>")
        if word_count:
            html_parts.append(f"<li>字数: {word_count}</li>")
        if serial_status:
            html_parts.append(f"<li>状态: {serial_status}</li>")

        html_parts.append("</ul>")
        html_parts.append("</div>")

        if summary:
            html_parts.append('<p class="new-page-after"><br/></p>')
            html_parts.append("<h2>简介</h2>")
            for paragraph in summary.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    html_parts.append(f"<p>{paragraph}</p>")

        return "\n".join(html_parts)

    def _build_epub(
        self,
        output_path: Path,
    ) -> Path | None:
        """
        Build an EPUB file at `output_path` from the given `book`.

        Returns Path on success, None on failure.
        """
        # make sure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # generate all the XML/XHTML strings up front
        container_xml = self._gen_container_xml()
        nav_xhtml = self.nav.to_xhtml()
        ncx_xml = self.ncx.to_xml()
        opf_xml = self.opf.to_xml()

        try:
            with zipfile.ZipFile(output_path, "w") as epub:
                # 1) The very first file must be the uncompressed mimetype
                epub.writestr(
                    "mimetype",
                    "application/epub+zip",
                    compress_type=ZIP_STORED,
                )

                # 2) META-INF/container.xml
                epub.writestr(
                    "META-INF/container.xml",
                    container_xml,
                    compress_type=ZIP_DEFLATED,
                )

                # 3) OEBPS/nav.xhtml, toc.ncx, content.opf
                epub.writestr(
                    f"{_ROOT_PATH}/nav.xhtml",
                    nav_xhtml,
                    compress_type=ZIP_DEFLATED,
                )
                epub.writestr(
                    f"{_ROOT_PATH}/toc.ncx",
                    ncx_xml,
                    compress_type=ZIP_DEFLATED,
                )
                epub.writestr(
                    f"{_ROOT_PATH}/content.opf",
                    opf_xml,
                    compress_type=ZIP_DEFLATED,
                )

                # 4) CSS files
                for css in self.stylesheets:
                    css_path = f"{_ROOT_PATH}/{_CSS_FOLDER}/{css.filename}"
                    epub.writestr(
                        css_path,
                        css.content,
                        compress_type=ZIP_DEFLATED,
                    )

                # 5) XHTML content items (chapters, etc.)
                for item in self.content_items:
                    chap_path = f"{_ROOT_PATH}/{_TEXT_FOLDER}/{item.filename}"
                    epub.writestr(
                        chap_path,
                        item.to_xhtml(),
                        compress_type=ZIP_DEFLATED,
                    )

                # 6) images
                for img in self.images:
                    img_path = f"{_ROOT_PATH}/{_IMAGE_FOLDER}/{img.filename}"
                    epub.writestr(
                        img_path,
                        img.data,  # bytes
                        compress_type=ZIP_DEFLATED,
                    )

            return output_path

        except Exception:
            return None

    @staticmethod
    def _hash_file(file_path: Path, chunk_size: int = 8192) -> str:
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

    @staticmethod
    def _gen_container_xml(
        root_path: str = _ROOT_PATH,
    ) -> str:
        """
        Generate the XML content for META-INF/container.xml in an EPUB archive.

        :param root_path: The folder where the OPF file is stored.
        :return: A string containing the full XML for container.xml.
        """
        return _CONTAINER_TEMPLATE.format(root_path=root_path)
