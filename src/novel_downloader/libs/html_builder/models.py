#!/usr/bin/env python3
"""
novel_downloader.libs.html_builder.models
-----------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

from .constants import CHAPTER_TEMPLATE


@dataclass(frozen=True)
class HtmlImage:
    filename: str
    data: bytes


@dataclass(frozen=True)
class HtmlChapter:
    filename: str
    title: str
    content: str

    def to_html(
        self,
        *,
        lang: str = "zh-Hans",
        prev_link: str = "",
        next_link: str = "",
    ) -> str:
        """
        Generate the HTML for a chapter.
        """
        return CHAPTER_TEMPLATE.format(
            lang=lang,
            title=escape(self.title),
            prev_link=prev_link,
            next_link=next_link,
            content=self.content,
        )


@dataclass
class HtmlVolume:
    title: str
    intro: str = ""
    chapters: list[HtmlChapter] = field(default_factory=list)
