#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.chapter_formatting
----------------------------------------------------

Format chapter content with title, paragraph blocks, and optional author notes.
"""

import re

_IMG_TAG_RE = re.compile(r"<img[^>]*>")


def format_chapter(title: str, paragraphs: str, author_say: str | None = None) -> str:
    """
    Build a formatted chapter string with title, paragraphs, and optional author note.

    :param title:       The chapter title.
    :param paragraphs:  Raw multi-line string; lines are treated as paragraphs.
    :param author_say:  Optional author comment to append at the end.
    :return:            A single string where title, paragraphs, and author note
                        are separated by blank lines.
    """
    parts: list[str] = [title.strip()]

    # add each nonempty paragraph line
    paragraphs = _IMG_TAG_RE.sub("", paragraphs)
    for ln in paragraphs.splitlines():
        line = ln.strip()
        if line:
            parts.append(line)

    # add author_say lines if present
    if author_say:
        author_lines = [ln.strip() for ln in author_say.splitlines() if ln.strip()]
        if author_lines:
            parts.append("---")
            parts.append("作者说:")
            parts.extend(author_lines)

    return "\n\n".join(parts)


__all__ = [
    "format_chapter",
]
