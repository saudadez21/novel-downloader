#!/usr/bin/env python3
"""
novel_downloader.libs.epub_builder.models
-----------------------------------------

Defines the core EPUB data models and resource classes used by the builder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .constants import (
    CHAP_TMPLATE,
    COVER_TEMPLATE,
    DEFAULT_FONT_FALLBACK_STACK,
    FONT_DIR,
    FONT_FACE_TEMPLATE,
    INTRO_TEMPLATE,
    NAV_TEMPLATE,
    NCX_TEMPLATE,
    OPF_TEMPLATE,
    VOLUME_COVER_TEMPLATE,
    VOLUME_INTRO_DESC_TEMPLATE,
    VOLUME_INTRO_TEMPLATE,
    VOLUME_TITLE_TEMPLATE,
    XHTML_TEMPLATE,
)


def escape_label(text: str) -> str:
    """Escape &, <, > for labels."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def escape_text(text: str) -> str:
    """Escape &, <, >, " and '."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    return text


@dataclass(slots=True)
class EpubResource:
    id: str
    filename: str
    media_type: str


@dataclass(slots=True)
class EpubImage(EpubResource):
    data: bytes


@dataclass(slots=True)
class EpubFont(EpubResource):
    data: bytes
    format: str
    family: str
    selectors: tuple[str, ...] | None = None

    @property
    def face_css(self) -> str:
        """Build the @font-face CSS rule for this font."""
        return FONT_FACE_TEMPLATE.format(
            family=self.family,
            filename=self.filename,
            format=self.format,
            font_dir=FONT_DIR,
        )


@dataclass(slots=True)
class EpubXhtmlFile(EpubResource):
    media_type: str = field(init=False, default="application/xhtml+xml")

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        """Subclasses MUST override."""
        raise NotImplementedError


@dataclass(slots=True)
class EpubCover(EpubXhtmlFile):
    ext: str = "jpg"
    id: str = field(init=False, default="cover")
    title: str = field(init=False, default="Cover")
    filename: str = field(init=False, default="cover.xhtml")

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        return COVER_TEMPLATE.format(
            lang=lang,
            title=self.title,
            ext=self.ext,
        )


@dataclass(slots=True)
class EpubVolumeCover(EpubXhtmlFile):
    title: str
    image_name: str

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        return VOLUME_COVER_TEMPLATE.format(
            lang=lang,
            title=escape_text(self.title),
            image_name=escape_text(self.image_name),
        )


@dataclass(slots=True)
class EpubVolumeTitle(EpubXhtmlFile):
    full_title: str

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        line1, line2 = self._split_volume_title(self.full_title)
        if not line1:
            line1, line2 = self.full_title, ""
        return VOLUME_TITLE_TEMPLATE.format(
            lang=lang,
            full_title=escape_text(self.full_title),
            line1=escape_text(line1),
            line2=escape_text(line2),
        )

    @staticmethod
    def _split_volume_title(title: str) -> tuple[str, str]:
        """
        Split volume title into two parts for better display.
        """
        separators = [" - ", "-", "：", ":", "—", "·", ".", " "]

        for sep in separators:
            if sep in title:
                parts = title.split(sep, 1)
                return parts[0].strip(), parts[1].strip()

        return "", title.strip()


@dataclass(slots=True)
class EpubXhtmlContent(EpubXhtmlFile):
    title: str
    content: str = ""
    fonts: list[EpubFont] = field(default_factory=list)

    default_selector: str = "body"

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        return XHTML_TEMPLATE.format(
            lang=lang,
            title=escape_text(self.title),
            font_styles=self._build_font_styles(),
            content=self.content,
        )

    def _collect_selectors(self) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for font in self.fonts:
            selectors = font.selectors or (self.default_selector,)
            for sel in selectors:
                mapping.setdefault(sel, []).append(font.family)
        return mapping

    def _build_font_styles(self) -> str:
        if not self.fonts:
            return ""

        blocks = ["<style>"]

        # 1. @font-face
        for font in self.fonts:
            blocks.append(font.face_css)

        # 2. selector rules
        selector_map = self._collect_selectors()
        for selector, families in selector_map.items():
            family_stack = ", ".join(f'"{f}"' for f in families)
            blocks.append(
                f"{selector} {{ font-family: {family_stack}, {DEFAULT_FONT_FALLBACK_STACK}; }}"  # noqa: E501
            )

        blocks.append("</style>")
        return "\n".join(blocks)


@dataclass(slots=True)
class EpubIntro(EpubXhtmlContent):
    book_title: str = ""
    author: str = ""
    description: str = ""
    subject: list[str] = field(default_factory=list)
    serial_status: str = ""
    word_count: str = "0"

    def _build_info_block(self) -> str:
        """Build the top info section with 书名/作者/字数/状态/标签."""
        parts: list[str] = []

        def add(label: str, value: str | None) -> None:
            if value:
                value = value.strip()
                if value:
                    parts.append(
                        f'<p><span class="label">{escape_text(label)}：</span>{escape_text(value)}</p>'  # noqa: E501
                    )

        add("书名", self.book_title)
        add("作者", self.author)

        if self.word_count and self.word_count != "0":
            add("字数", self.word_count)

        if self.serial_status:
            add("状态", self.serial_status)

        if self.subject:
            tag_str = "，".join(escape_text(t) for t in self.subject)
            parts.append(f'<p><span class="label">标签：</span>{tag_str}</p>')

        return "\n".join(parts)

    def _build_description_block(self) -> str:
        """Build the 简介 section from builder.description."""
        if not self.description or not self.description.strip():
            return ""

        paras = [
            f"<p>{escape_text(line.strip())}</p>"
            for line in self.description.splitlines()
            if line.strip()
        ]
        if not paras:
            return ""

        return (
            "<br />\n"
            '<h2 class="intro-title">简介</h2>\n'
            '<div class="intro-description">\n' + "\n".join(paras) + "\n</div>"
        )

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        info_block = self._build_info_block()
        description_block = self._build_description_block()
        return INTRO_TEMPLATE.format(
            lang=lang,
            title=escape_text(self.title),
            font_styles=self._build_font_styles(),
            info_block=info_block,
            description_block=description_block,
        )


@dataclass(slots=True)
class EpubVolumeIntro(EpubXhtmlContent):
    description: str = ""

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        # description is expected as HTML, e.g. "<p>第一段。</p><p>第二段。</p>"
        return VOLUME_INTRO_TEMPLATE.format(
            lang=lang,
            title=escape_text(self.title),
            font_styles=self._build_font_styles(),
            description=self._build_description_block(),
        )

    def _build_description_block(self) -> str:
        paras = [
            f"<p>{escape_text(line.strip())}</p>"
            for line in self.description.splitlines()
            if line.strip()
        ]
        if not paras:
            return ""
        return "\n".join(paras)


@dataclass(slots=True)
class EpubVolumeIntroDesc(EpubXhtmlContent):
    description: str = ""

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        return VOLUME_INTRO_DESC_TEMPLATE.format(
            lang=lang,
            title=escape_text(self.title),
            font_styles=self._build_font_styles(),
            description=self._build_description_block(),
        )

    def _build_description_block(self) -> str:
        paras = [
            f"<p>{escape_text(line.strip())}</p>"
            for line in self.description.splitlines()
            if line.strip()
        ]
        if not paras:
            return ""
        return "\n".join(paras)


@dataclass(slots=True)
class EpubChapter(EpubXhtmlContent):
    default_selector: str = ".chapter-content"
    extra_content: str = ""

    def to_xhtml(self, lang: str = "zh-Hans") -> str:
        """Generate the XHTML for a chapter."""
        return CHAP_TMPLATE.format(
            lang=lang,
            title=escape_text(self.title),
            font_styles=self._build_font_styles(),
            content=self.content,
            extra_block=self._build_extra_block(),
        )

    def _build_extra_block(self) -> str:
        if not self.extra_content:
            return ""
        return f'<br />\n<div class="extra-block">\n{self.extra_content}\n</div>'


@dataclass(slots=True)
class EpubVolume:
    id: str
    title: str
    intro: str = ""
    cover_path: Path | None = None
    chapters: list[EpubChapter] = field(default_factory=list)


@dataclass(slots=True)
class NavDocument(EpubResource):
    title: str = "未命名"
    language: str = "zh-Hans"
    id: str = "nav"
    filename: str = "nav.xhtml"
    media_type: str = field(init=False, default="application/xhtml+xml")
    lines: list[str] = field(default_factory=list)

    def add_chapter(self, id: str, label: str, src: str) -> None:
        """
        Add a top-level chapter entry to the navigation.

        :param id: The unique ID for the chapter.
        :param label: The display title for the chapter.
        :param src: The href target for the chapter's XHTML file.
        """
        label = escape_label(label)
        self.lines.append(f'<li><a href="{src}">{label}</a></li>')

    def add_volume(
        self,
        id: str,
        label: str,
        src: str,
        chapters: list[tuple[str, str, str]],
    ) -> None:
        """
        Add a volume entry with nested chapters to the navigation.

        :param id: The unique ID for the volume.
        :param label: The display title for the volume.
        :param src: The href target for the volume's intro XHTML file.
        :param chapters: A list of chapter entries under this volume.
        """
        label = escape_label(label)

        self.lines.append(f'<li><a href="{src}">{label}</a>\n<ol>')

        for _, clabel, csrc in chapters:
            clabel = escape_label(clabel)
            self.lines.append(f'<li><a href="{csrc}">{clabel}</a></li>')

        self.lines.append("</ol>\n</li>")

    def to_xhtml(self) -> str:
        """
        Generate the XHTML content for nav.xhtml based on the NavDocument.

        :return: A string containing the full XHTML for nav.xhtml.
        """
        items = "\n".join(self.lines)
        return NAV_TEMPLATE.format(
            lang=self.language,
            id=self.id,
            title=escape_label(self.title),
            items=items,
        )

    def clear(self) -> None:
        self.lines.clear()


@dataclass(slots=True)
class NCXDocument(EpubResource):
    title: str = "未命名"
    uid: str = ""
    id: str = "ncx"
    filename: str = "toc.ncx"
    media_type: str = field(init=False, default="application/x-dtbncx+xml")
    lines: list[str] = field(default_factory=list)

    _order: int = 1

    def add_chapter(self, id: str, label: str, src: str) -> None:
        self.lines.append(self._nav(id, label, src))

    def add_volume(
        self, id: str, label: str, src: str, chapters: list[tuple[str, str, str]]
    ) -> None:
        label = escape_label(label)
        order = self._order
        self._order += 1

        self.lines.append(
            f'<navPoint id="{id}" playOrder="{order}">'
            f"<navLabel><text>{label}</text></navLabel>"
            f'<content src="{src}"/>'
        )
        nav = self._nav
        for cid, clabel, csrc in chapters:
            self.lines.append(nav(cid, clabel, csrc))
        self.lines.append("</navPoint>")

    def to_xml(self) -> str:
        """
        Generate the XML content for toc.ncx used in EPUB 2 navigation.

        :return: A string containing the full NCX XML document.
        """
        navpoints = "\n".join(self.lines)
        depth = 2  # always 1 level or 2 levels

        return NCX_TEMPLATE.format(
            uid=self.uid,
            depth=depth,
            title=self.title,
            navpoints=navpoints,
        )

    def _nav(self, id: str, label: str, src: str) -> str:
        label = escape_label(label)
        order = self._order
        self._order += 1
        return (
            f'<navPoint id="{id}" playOrder="{order}">'
            f"<navLabel><text>{label}</text></navLabel>"
            f'<content src="{src}"/>'
            f"</navPoint>"
        )


@dataclass(slots=True)
class OpfDocument(EpubResource):
    # resource identity
    id: str = "opf"
    filename: str = "content.opf"
    media_type: str = field(init=False, default="application/oebps-package+xml")

    # metadata fields
    title: str = ""
    author: str = ""
    description: str = ""
    uid: str = ""
    subject: list[str] = field(default_factory=list)
    language: str = "zh-Hans"

    # internal state
    manifest_lines: list[str] = field(default_factory=list)
    spine_lines: list[str] = field(default_factory=list)

    _cover_item_id: str | None = field(init=False, default=None)
    _toc_item_id: str | None = field(init=False, default=None)

    def add_manifest_item(
        self,
        id: str,
        href: str,
        media_type: str,
        properties: str | None = None,
    ) -> None:
        prop_attr = f' properties="{properties}"' if properties else ""
        self.manifest_lines.append(
            f'<item id="{id}" href="{href}" media-type="{media_type}"{prop_attr}/>'
        )

        if properties == "cover-image":
            self._cover_item_id = id
        if media_type == "application/x-dtbncx+xml":
            self._toc_item_id = id

    def add_spine_item(
        self,
        idref: str,
        properties: str | None = None,
    ) -> None:
        prop_attr = f' properties="{properties}"' if properties else ""
        self.spine_lines.append(f'<itemref idref="{idref}"{prop_attr}/>')

    def to_xml(self) -> str:
        """
        Generate the content.opf XML, which defines metadata, manifest, and spine.

        This function outputs a complete OPF package document that includes:
          * <metadata>: title, author, language, identifiers, etc.
          * <manifest>: all resource entries
          * <spine>: the reading order of the content

        :return: A string containing the full OPF XML content.
        """
        from datetime import UTC, datetime

        now_iso = (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )

        # ---------- metadata ----------
        meta = []
        meta.append(f'<meta property="dcterms:modified">{now_iso}</meta>')
        meta.append(f'<dc:identifier id="id">{self.uid}</dc:identifier>')
        meta.append(f"<dc:title>{escape_text(self.title)}</dc:title>")
        meta.append(f"<dc:language>{self.language}</dc:language>")

        if self.author:
            meta.append(
                f'<dc:creator id="creator">{escape_text(self.author)}</dc:creator>'
            )
            meta.append(
                '<meta refines="#creator" property="role" scheme="marc:relators">aut</meta>'  # noqa: E501
            )

        if self.description:
            meta.append(
                f"<dc:description>{escape_text(self.description)}</dc:description>"
            )

        if self.subject:
            meta.append(
                f"<dc:subject>{escape_text(','.join(self.subject))}</dc:subject>"
            )

        if self._cover_item_id:
            meta.append(f'<meta name="cover" content="{self._cover_item_id}"/>')

        metadata = "\n".join(meta)

        # ---------- manifest ----------
        manifest_items = "\n".join(self.manifest_lines)

        # ---------- spine ----------
        toc_attr = f' toc="{self._toc_item_id}"' if self._toc_item_id else ""
        spine_items = "\n".join(self.spine_lines)

        return OPF_TEMPLATE.format(
            metadata=metadata,
            manifest_items=manifest_items,
            spine_toc=toc_attr,
            spine_items=spine_items,
        )
