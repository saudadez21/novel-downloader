#!/usr/bin/env python3
"""
novel_downloader.libs.html_builder.models
-----------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

from .constants import (
    CHAPTER_TEMPLATE,
    DEFAULT_FONT_FALLBACK_STACK,
    FONT_DIR,
    FONT_FACE_TEMPLATE,
    FONT_FORMAT_MAP,
)


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


@dataclass
class HtmlVolume:
    title: str
    intro: str = ""
    chapters: list[HtmlChapter] = field(default_factory=list)
