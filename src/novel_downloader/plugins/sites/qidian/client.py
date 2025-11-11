#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.client
--------------------------------------------
"""

import asyncio
from html import escape
from typing import Any

from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict


@registrar.register_client()
class QidianClient(CommonClient):
    """
    Specialized client for 起点 novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    @staticmethod
    def _check_restricted(html_list: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. not subscribed/purchased).

        :param html_list: Raw HTML string.
        """
        if not html_list:
            return True
        markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
        return any(m in html_list[0] for m in markers)

    @staticmethod
    def _check_encrypted(html_list: list[str]) -> bool:
        if not html_list:
            return True
        return '"cES":2' in html_list[0]

    def _need_refetch(self, chap: ChapterDict) -> bool:
        return bool(chap.get("extra", {}).get("encrypted", False))

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
    ) -> ChapterDict | None:
        """
        Fetch, debug-save, parse a single chapter with retries.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self._retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                if self._check_restricted(html_list):
                    self.logger.info(
                        "qidian: restricted chapter content (book=%s, chapter=%s)",
                        book_id,
                        cid,
                    )
                    return None
                encrypted = self._check_encrypted(html_list)

                folder = "html_encrypted" if encrypted else "html_plain"
                self._save_html_pages(book_id, cid, html_list, folder=folder)

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if encrypted and not chap:
                    self.logger.info(
                        "qidian: failed to parse encrypted chapter (book=%s, chapter=%s)",  # noqa: E501
                        book_id,
                        cid,
                    )
                    return None
                if not chap:
                    raise ValueError("Empty parse result")
                return chap

            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info(
                        "qidian: retrying chapter (book=%s, chapter=%s, attempt=%s): %s",  # noqa: E501
                        book_id,
                        cid,
                        attempt + 1,
                        e,
                    )
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff,
                        mul_spread=1.2,
                        max_sleep=backoff + 3,
                    )
                else:
                    self.logger.warning(
                        "qidian: failed chapter (book=%s, chapter=%s): %s",
                        book_id,
                        cid,
                        e,
                    )
        return None

    def _render_txt_extras(self, extras: dict[str, Any]) -> str:
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

    def _render_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        Render "作者说" section for EPUB.

        Clean text, wrap as HTML-safe, and format with heading.
        """
        note = (extras.get("author_say") or "").strip()
        if not note:
            return ""

        parts = [
            "<hr />",
            "<h3>作者说</h3>",
            *(f"<p>{escape(s)}</p>" for ln in note.splitlines() if (s := ln.strip())),
        ]
        return "\n".join(parts)

    def _render_html_extras(self, extras: dict[str, Any]) -> str:
        return self._render_epub_extras(extras)
