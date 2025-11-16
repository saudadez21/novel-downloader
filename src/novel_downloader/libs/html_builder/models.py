#!/usr/bin/env python3
"""
novel_downloader.libs.html_builder.models
-----------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import (
    CHAPTER_DIR,
    CHAPTER_TEMPLATE,
    DEFAULT_FONT_FALLBACK_STACK,
    FONT_DIR,
    FONT_FACE_TEMPLATE,
    FONT_FORMAT_MAP,
    INDEX_TEMPLATE,
    MEDIA_DIR,
)


def escape(text: str) -> str:
    """Escape &, <, > for text-node HTML."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    return text


@dataclass(frozen=True)
class HtmlImage:
    filename: str
    data: bytes


@dataclass(frozen=True)
class HtmlFont:
    filename: str
    data: bytes
    family: str
    selectors: tuple[str, ...] = field(default_factory=tuple)

    def _font_format(self) -> str:
        """Best-effort guess for CSS `format()` from filename extension."""
        ext = self.filename.rsplit(".", 1)[-1].lower()
        return FONT_FORMAT_MAP.get(ext, "truetype")

    @property
    def effective_selectors(self) -> tuple[str, ...]:
        """Use user-provided selectors, or default to '.chapter-content'."""
        if self.selectors:
            return self.selectors
        return (".chapter-content",)

    def build_css(self, *, font_url_prefix: str) -> str:
        """Build the CSS content for this font."""
        return FONT_FACE_TEMPLATE.format(
            family=self.family,
            url=f"{font_url_prefix}{self.filename}",
            format=self._font_format(),
        )


@dataclass(frozen=True)
class HtmlChapter:
    filename: str
    title: str
    content: str
    extra_content: str = ""
    fonts: list[HtmlFont] = field(default_factory=list)

    def to_html(
        self,
        *,
        lang: str = "zh-Hans",
        prev_link: str = "",
        next_link: str = "",
    ) -> str:
        """Generate the HTML for a chapter."""
        return CHAPTER_TEMPLATE.format(
            lang=lang,
            title=escape(self.title),
            prev_link=prev_link,
            next_link=next_link,
            content=self.content,
            extra_block=self._build_extra_block(),
            font_styles=self._build_font_styles(),
        )

    def _collect_selectors(self) -> dict[str, list[str]]:
        """
        Collects mapping of selector -> list of font-family names.

        e.g. ``{".chapter-content": ["MyObfA", "MyObfB"]}``
        """
        mapping: dict[str, list[str]] = {}
        for font in self.fonts:
            for sel in font.effective_selectors:
                mapping.setdefault(sel, []).append(font.family)
        return mapping

    def _build_font_styles(self) -> str:
        """Build the <style> block for all fonts in this chapter."""
        if not self.fonts:
            return ""
        blocks: list[str] = ["<style>"]

        # Emit all @font-face blocks first
        prefix = f"../{FONT_DIR}/"
        for font in self.fonts:
            blocks.append(font.build_css(font_url_prefix=prefix))

        # Build selector -> font-family rules
        selector_map = self._collect_selectors()
        for selector, families in selector_map.items():
            family_stack = ", ".join(f'"{name}"' for name in families)
            family_stack += f", {DEFAULT_FONT_FALLBACK_STACK}"
            blocks.append(f"{selector} {{ font-family: {family_stack}; }}")

        blocks.append("</style>")
        return "\n".join(blocks)

    def _build_extra_block(self) -> str:
        if not self.extra_content:
            return ""
        return f'<div class="extra-block">\n{self.extra_content}\n</div>'


@dataclass
class HtmlVolume:
    title: str
    intro: str = ""
    chapters: list[HtmlChapter] = field(default_factory=list)


@dataclass(slots=True)
class IndexDocument:
    # metadata
    title: str = ""
    author: str = ""
    description: str = ""
    subject: list[str] = field(default_factory=list)
    serial_status: str = ""
    word_count: str = "0"
    lang: str = "zh-Hans"

    # computed / runtime state
    cover_filename: str | None = None
    toc_blocks: list[str] = field(init=False, default_factory=list)

    def clear(self) -> None:
        self.toc_blocks.clear()

    def add_volume(self, volume: HtmlVolume) -> None:
        """Append a volume section (with its chapters) into the TOC."""
        parts: list[str] = []
        parts.append(f'<section class="volume">\n  <h3>{escape(volume.title)}</h3>')

        if volume.intro:
            parts.append(f'  <p class="volume-intro">{escape(volume.intro)}</p>')

        if volume.chapters:
            parts.append("  <ul>")
            for chap in volume.chapters:
                href = f"{CHAPTER_DIR}/{chap.filename}"
                parts.append(f'    <li><a href="{href}">{escape(chap.title)}</a></li>')
            parts.append("  </ul>")

        parts.append("</section>")
        self.toc_blocks.append("\n".join(parts))

    def add_chapter(self, chap: HtmlChapter) -> None:
        """
        Append a standalone chapter (not part of any volume) into the TOC.

        We reuse the same .volume + <ul> structure so existing CSS continues
        to work; each standalone chapter is rendered as its own small section.
        """
        href = f"{CHAPTER_DIR}/{chap.filename}"
        title = escape(chap.title)

        block = (
            f'<section class="volume">\n'
            f"  <h3>{title}</h3>\n"
            f"  <ul>\n"
            f'    <li><a href="{href}">{title}</a></li>\n'
            f"  </ul>\n"
            f"</section>"
        )
        self.toc_blocks.append(block)

    def _build_header_html(self) -> str:
        header_parts: list[str] = []

        # Title
        header_parts.append(f"<h1>{escape(self.title)}</h1>")

        # Author
        if self.author:
            header_parts.append(f'<p class="author">作者：{escape(self.author)}</p>')

        # Cover (if any)
        if self.cover_filename:
            header_parts.append(
                f'<img src="{MEDIA_DIR}/{self.cover_filename}" '
                f'alt="封面" class="cover">'
            )

        # Meta: 状态 / 字数
        meta_bits: list[str] = []
        if self.serial_status:
            meta_bits.append(f"状态：{escape(self.serial_status)}")
        if self.word_count:
            meta_bits.append(f"字数：{escape(str(self.word_count))}")
        if meta_bits:
            header_parts.append(f'<p class="meta">{"　".join(meta_bits)}</p>')

        # Tags
        if self.subject:
            tags_str = " / ".join(escape(tag) for tag in self.subject)
            header_parts.append(f'<p class="tags">标签：{tags_str}</p>')

        # Description
        if self.description:
            header_parts.append(
                f'<p class="description">{escape(self.description)}</p>'
            )

        return "\n    ".join(header_parts)

    def to_html(self) -> str:
        """Generate the full HTML for index.html using INDEX_TEMPLATE."""
        header_html = self._build_header_html()
        toc_html = "\n".join(self.toc_blocks)

        return INDEX_TEMPLATE.format(
            lang=self.lang,
            book_name=escape(self.title),
            header=header_html,
            toc_html=toc_html,
        )
