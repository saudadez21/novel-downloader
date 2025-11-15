#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.client
--------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict


@registrar.register_client()
class QqbookClient(CommonClient):
    """
    Specialized client for QQ 阅读 novel sites.
    """

    ASCII_SET = {chr(i) for i in range(256)}

    @property
    def workers(self) -> int:
        return 1

    def _dl_check_refetch(self, chap: ChapterDict) -> bool:
        """
        Return True if the chapter is marked as font-encrypted
        and should be upserted with need_refetch=True.
        """
        return bool(chap.get("extra", {}).get("font_encrypt", False))

    def _xp_epub_chap_post(self, html_parts: list[str], chap: ChapterDict) -> list[str]:
        refl_list = chap["extra"].get("refl_list", [])
        refl_set = set(refl_list) - self.ASCII_SET
        for i in range(len(html_parts)):
            html_parts[i] = self._xp_apply_refl_list(html_parts[i], refl_set)
        return html_parts

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
