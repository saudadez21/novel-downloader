#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.downloader
--------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.common.downloader import CommonDownloader
from novel_downloader.plugins.registry import registrar


@registrar.register_downloader()
class CiyuanjiDownloader(CommonDownloader):
    """
    Specialized downloader for 次元姬 novels.

    Processes each chapter in a single worker that skip non-accessible
    and handles fetch -> parse -> enqueue storage.
    """

    @property
    def workers(self) -> int:
        return 1

    def _extract_img_urls(self, extra: dict[str, Any]) -> list[str]:
        img_list = extra.get("imgList", [])
        if not isinstance(img_list, list):
            return []
        return [
            url
            for item in img_list
            if isinstance(item, dict) and isinstance((url := item.get("imgUrl")), str)
        ]
