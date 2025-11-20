#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciweimao.client
----------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class CiweimaoClient(CommonClient):
    """
    Specialized client for ciweimao novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    def _xp_txt_extras(self, extras: dict[str, Any]) -> str:
        """
        render "作者说" for TXT:
          * Clean content
          * Strip leading/trailing blanks
          * Drop multiple blank lines (keep only non-empty lines)
        """
        note = (extras.get("author_say") or "").strip()
        if not note:
            return ""

        # collapse blank lines
        body = "\n".join(s for line in note.splitlines() if (s := line.strip()))
        return f"作者说\n\n{body}"

    def _xp_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        Render "作者说" section for EPUB.

        Clean text, wrap as HTML-safe, and format with heading.
        """
        note = extras.get("author_say")
        if not note:
            return ""

        out = ["<h3>作者说</h3>"]

        for ln in note.splitlines():
            ln = ln.strip()
            if not ln:
                continue

            if "<" in ln or ">" in ln or "&" in ln:
                ln = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            out.append(f"<p>{ln}</p>")

        return "\n".join(out)

    def _xp_html_extras(self, extras: dict[str, Any]) -> str:
        return self._xp_epub_extras(extras)
