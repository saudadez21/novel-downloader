#!/usr/bin/env python3
"""
novel_downloader.core.exporters.txt_util
----------------------------------------

Utilities for generating plain-text exports of novel content.
"""

__all__ = [
    "build_txt_header",
    "build_txt_chapter",
]

import re

_IMG_TAG_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)


def build_txt_header(fields: list[tuple[str, str]]) -> str:
    """
    Build a simple text header from label-value pairs, followed by a dashed separator.

    :param fields: List of (label, value) pairs.
    :return: A single string containing the formatted header.
    """
    header_lines = [f"{label}: {value}" for label, value in fields if value]
    header_lines += ["", "-" * 10, ""]
    return "\n".join(header_lines)


def build_txt_chapter(
    title: str,
    paragraphs: str,
    extras: dict[str, str] | None = None,
) -> str:
    """
    Build a formatted chapter text block including title, body paragraphs,
    and optional extra sections.

      * Strips any `<img...>` tags from paragraphs.
      * Title appears first (stripped of surrounding whitespace).
      * Each non-blank line in `paragraphs` becomes its own paragraph.

    :param title: Chapter title.
    :param paragraphs: Raw multi-line string. Blank lines are ignored.
    :param extras: Optional dict mapping section titles to multi-line strings.
    :return: A string where title, paragraphs, and extras are joined by lines.
    """
    parts: list[str] = [title.strip()]

    # add each nonempty paragraph line
    paragraphs = _IMG_TAG_RE.sub("", paragraphs)
    for ln in paragraphs.splitlines():
        line = ln.strip()
        if line:
            parts.append(line)

    if extras:
        for title, text in extras.items():
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if not lines:
                continue
            parts.append("---")
            parts.append(title.strip())
            parts.extend(lines)

    return "\n\n".join(parts)
