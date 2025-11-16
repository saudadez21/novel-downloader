#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.client
--------------------------------------------
"""

import asyncio
import logging
from typing import Any

from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict

logger = logging.getLogger(__name__)


@registrar.register_client()
class QidianClient(CommonClient):
    """
    Specialized client for 起点 novel sites.
    """

    ASCII_SET = {chr(i) for i in range(256)}

    @property
    def workers(self) -> int:
        return 1

    @staticmethod
    def _check_restricted(raw_pages: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. not subscribed/purchased).

        :param raw_pages: Raw HTML string.
        """
        if not raw_pages:
            return True
        markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
        return any(m in raw_pages[0] for m in markers)

    @staticmethod
    def _check_encrypted(raw_pages: list[str]) -> bool:
        if not raw_pages:
            return True
        return '"cES":2' in raw_pages[0]

    def _dl_check_refetch(self, chap: ChapterDict) -> bool:
        return bool(chap.get("extra", {}).get("encrypted", False))

    async def get_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Fetch, debug-save, parse a single chapter with retries.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self._retry_times + 1):
            try:
                raw_pages = await self.fetcher.fetch_chapter_content(
                    book_id, chapter_id
                )
                if self._check_restricted(raw_pages):
                    logger.info(
                        "qidian: restricted chapter content (book=%s, chapter=%s)",
                        book_id,
                        chapter_id,
                    )
                    return None
                encrypted = self._check_encrypted(raw_pages)

                folder = "html_encrypted" if encrypted else "html_plain"
                self._save_raw_pages(book_id, chapter_id, raw_pages, folder=folder)

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter_content, raw_pages, chapter_id
                )
                if encrypted and not chap:
                    logger.info(
                        "qidian: failed to parse encrypted chapter (book=%s, chapter=%s)",  # noqa: E501
                        book_id,
                        chapter_id,
                    )
                    return None
                if not chap:
                    raise ValueError("Empty parse result")

                resources = chap["extra"].get("resources")
                if resources:
                    media_dir = self._raw_data_dir / book_id / "media"
                    await self.fetcher.fetch_media(media_dir, resources)

                return chap

            except Exception as e:
                if attempt < self._retry_times:
                    logger.info(
                        "qidian: retrying chapter (book=%s, chapter=%s, attempt=%s): %s",  # noqa: E501
                        book_id,
                        chapter_id,
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
                    logger.warning(
                        "qidian: failed chapter (book=%s, chapter=%s): %s",
                        book_id,
                        chapter_id,
                        e,
                    )
        return None

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

    def _xp_epub_chap_post(self, html_parts: list[str], chap: ChapterDict) -> list[str]:
        refl_list = chap["extra"].get("refl_list", [])
        refl_set = set(refl_list) - self.ASCII_SET
        for i in range(len(html_parts)):
            html_parts[i] = self._xp_apply_refl_list(html_parts[i], refl_set)
        return html_parts

    def _xp_html_extras(self, extras: dict[str, Any]) -> str:
        return self._xp_epub_extras(extras)

    def _xp_html_chap_post(self, html_parts: list[str], chap: ChapterDict) -> list[str]:
        refl_list = chap["extra"].get("refl_list", [])
        refl_set = set(refl_list) - self.ASCII_SET
        for i in range(len(html_parts)):
            html_parts[i] = self._xp_apply_refl_list(html_parts[i], refl_set)
        return html_parts

    @staticmethod
    def _xp_apply_refl_list(raw: str, refl_set: set[str]) -> str:
        """"""
        for ch in refl_set:
            raw = raw.replace(ch, f'<span class="refl">{ch}</span>')
        return raw
