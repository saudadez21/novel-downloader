#!/usr/bin/env python3
"""
novel_downloader.plugins.processors.translator.google
-----------------------------------------------------
"""

from __future__ import annotations

import copy
import logging
import time
from typing import Any

import requests

from novel_downloader.infra.http_defaults import DEFAULT_USER_AGENT
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import BookInfoDict, ChapterDict

logger = logging.getLogger(__name__)


@registrar.register_processor()
class GoogleTranslaterProcessor:
    """
    Translate novel metadata and chapters using the Google Translate endpoint.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._source: str = config.get("source") or "auto"
        self._target: str = config.get("target") or "zh-CN"
        self._sleep: float = float(config.get("sleep", 2.0))
        self._endpoint = "https://translate.googleapis.com/translate_a/single"
        self._headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": DEFAULT_USER_AGENT,
        }

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        """
        Apply translate to book metadata and nested structures.
        """
        bi = copy.deepcopy(book_info)
        bi["book_name"] = self._translate(bi.get("book_name", ""))
        bi["summary"] = self._translate(bi.get("summary", ""))

        if "summary_brief" in bi:
            bi["summary_brief"] = self._translate(bi["summary_brief"])

        for vol in bi.get("volumes", []):
            vol["volume_name"] = self._translate(vol.get("volume_name", ""))
            if "volume_intro" in vol:
                vol["volume_intro"] = self._translate(vol["volume_intro"])
            for ch in vol.get("chapters", []):
                ch["title"] = self._translate(ch.get("title", ""))

        return bi

    def process_chapter(self, chapter: ChapterDict) -> ChapterDict:
        """
        Apply cleaning rules to a single chapter (title + content).
        """
        ch = copy.deepcopy(chapter)
        ch["title"] = self._translate(ch.get("title", ""))
        ch["content"] = self._translate(ch.get("content", ""))
        return ch

    def _translate(self, text: str) -> str:
        """Send text to the unofficial Google Translate endpoint."""
        if not text.strip():
            return text

        data = {
            "client": "gtx",
            "sl": self._source,
            "tl": self._target,
            "dt": "t",
            "dj": "1",
            "q": text,
        }
        trans: str = text

        try:
            r = requests.post(
                self._endpoint, data=data, headers=self._headers, timeout=20
            )
            if r.status_code == 200:
                resp = r.json()
                trans = "".join(s["trans"] for s in resp["sentences"])
            else:
                logger.warning(
                    "HTTP %d while translating text: %s",
                    r.status_code,
                    r.text,
                )
        except Exception as e:
            logger.warning("Translation request failed: %s", e)

        # Respectful delay between requests
        time.sleep(self._sleep)

        return trans
