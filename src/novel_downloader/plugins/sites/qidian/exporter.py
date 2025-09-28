#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.exporter
----------------------------------------------

Exporter implementation for Qidian novels, supporting plain and encrypted sources.
"""

__all__ = ["QidianExporter"]

from typing import Any, ClassVar

from novel_downloader.plugins.common.exporter import CommonExporter
from novel_downloader.plugins.registry import registrar


@registrar.register_exporter()
class QidianExporter(CommonExporter):
    """
    Exporter for Qidian (起点) novels.
    """

    DEFAULT_SOURCE_ID: ClassVar[int] = 0
    ENCRYPTED_SOURCE_ID: ClassVar[int] = 1
    PRIORITIES_MAP: ClassVar[dict[int, int]] = {
        DEFAULT_SOURCE_ID: 0,
        ENCRYPTED_SOURCE_ID: 1,
    }

    def _render_txt_extras(self, extras: dict[str, Any]) -> str:
        """
        render "作者说" for TXT:
          * Clean content
          * Strip leading/trailing blanks
          * Drop multiple blank lines (keep only non-empty lines)
        """
        note = self._cleaner.clean_content(extras.get("author_say") or "").strip()
        if not note:
            return ""

        # collapse blank lines
        body = "\n".join(s for line in note.splitlines() if (s := line.strip()))
        return f"作者说\n\n{body}"

    def _render_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        render "作者说" for EPUB:
          * Clean content
          * Keep as HTML-safe via _render_html_block
          * Wrap with `<hr/>` + `<h3>作者说</h3>`
        """
        note = self._cleaner.clean_content(extras.get("author_say") or "").strip()
        if not note:
            return ""

        parts = [
            "<hr />",
            "<h3>作者说</h3>",
            self._render_html_block(note),
        ]
        return "\n".join(parts)
