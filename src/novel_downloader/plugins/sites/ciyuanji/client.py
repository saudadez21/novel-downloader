#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.client
----------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict


@registrar.register_client()
class CiyuanjiClient(CommonClient):
    """
    Specialized client for 次元姬 novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    def _collect_img_map(self, chap: ChapterDict) -> dict[int, list[dict[str, Any]]]:
        """
        Collect and normalize all images into {int: [ {type, data, ...}, ... ]}.
        """
        out: dict[int, list[dict[str, Any]]] = {}
        extra = chap.get("extra") or {}

        # ---- imgList ----
        img_list = extra.get("imgList")
        if isinstance(img_list, list):
            for item in img_list:
                if not isinstance(item, dict):
                    continue

                idx = item.get("paragraphIndex")
                url = item.get("imgUrl")
                if not (isinstance(idx, int) and isinstance(url, str)):
                    continue

                entry: dict[str, Any] = {
                    "type": "url",
                    "data": url.strip(),
                }
                if name := item.get("imgName"):
                    entry["name"] = str(name)
                if width := item.get("width"):
                    try:
                        entry["width"] = int(width)
                    except Exception:
                        entry["width"] = width
                if height := item.get("height"):
                    try:
                        entry["height"] = int(height)
                    except Exception:
                        entry["height"] = height

                out.setdefault(idx, []).append(entry)

        # ---- wordList ----
        word_list = extra.get("wordList")
        if isinstance(word_list, list):
            for item in word_list:
                if not isinstance(item, dict):
                    continue

                idx = item.get("paragraphIndex")
                url = item.get("imgUrl")
                if not (isinstance(idx, int) and isinstance(url, str)):
                    continue

                out.setdefault(idx, []).append(
                    {
                        "type": "url",
                        "data": url.strip(),
                    }
                )

        return out
