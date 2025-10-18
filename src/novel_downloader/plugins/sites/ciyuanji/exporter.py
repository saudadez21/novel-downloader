#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.exporter
------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.common.exporter import CommonExporter
from novel_downloader.plugins.registry import registrar


@registrar.register_exporter()
class CiyuanjiExporter(CommonExporter):
    """
    Exporter for Ciyuanji (次元姬) novels.
    """

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
