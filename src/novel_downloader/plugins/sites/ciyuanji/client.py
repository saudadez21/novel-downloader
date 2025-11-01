#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.client
----------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class CiyuanjiClient(CommonClient):
    """
    Specialized client for 次元姬 novel sites.
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

    @staticmethod
    def _collect_img_map(extras: dict[str, Any]) -> dict[int, list[str]]:
        """
        Convert `extras["imgList"]` into `{int -> [url, ...]}`.
        """
        out: dict[int, list[str]] = {}
        img_list = extras.get("imgList")
        if not isinstance(img_list, list):
            return out
        for item in img_list:
            if not isinstance(item, dict):
                continue
            idx = item.get("paragraphIndex")
            url = item.get("imgUrl")
            if isinstance(idx, int) and isinstance(url, str):
                u = url.strip()
                if u:
                    out.setdefault(idx, []).append(u)
        return out
