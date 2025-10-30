#!/usr/bin/env python3
"""
novel_downloader.plugins.processors.translator.edge
---------------------------------------------------
"""

import base64
import copy
import json
import logging
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import requests

from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import BookInfoDict, ChapterDict

logger = logging.getLogger(__name__)


@registrar.register_processor()
class EdgeTranslaterProcessor:
    """
    Translate book and chapter data using the Microsoft Edge Translator.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._source: str = config.get("source") or "auto"
        self._target: str = config.get("target") or "zh-Hans"
        self._sleep: float = float(config.get("sleep", 1.0))
        self._endpoint: str = (
            "https://api-edge.cognitive.microsofttranslator.com/translate"
        )
        self._auth_url: str = "https://edge.microsoft.com/translate/auth"
        self._token_cache: dict[str, Any] | None = None

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        """
        Translate book metadata and nested structures.
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
        Translate a single chapter (title + content).
        Each line is treated as one paragraph.
        """
        ch = copy.deepcopy(chapter)

        ch["title"] = self._translate(ch.get("title", ""))

        paragraphs = self._split_text(ch.get("content", ""))
        translated = [self._translate(p) for p in paragraphs]
        ch["content"] = "\n".join(translated)

        return ch

    @staticmethod
    def _split_text(text: str, max_length: int = 3000) -> list[str]:
        """
        Each line is treated as one paragraph.
        """
        lines = [ln for line in text.splitlines() if (ln := line.strip())]
        chunks: list[str] = []
        buf: list[str] = []
        buf_len = 0

        for line in lines:
            line_len = len(line)
            if buf_len + line_len + (1 if buf else 0) <= max_length:
                buf.append(line)
                buf_len += line_len + (1 if buf_len > 0 else 0)
            else:
                if buf:
                    chunks.append("\n".join(buf))
                buf = [line]
                buf_len = line_len

        if buf:
            chunks.append("\n".join(buf))

        return chunks

    def _parse_jwt(self, token: str) -> dict[str, Any]:
        """
        Parse Edge's JWT token to extract expiration time.
        """
        parts = token.split(".")
        if len(parts) < 2:
            raise ValueError("Invalid JWT token returned by Edge auth endpoint.")
        base64_url = parts[1].replace("-", "+").replace("_", "/")
        decoded = base64.b64decode(base64_url + "===")
        payload = json.loads(decoded)
        return {
            "token": token,
            "expire": datetime.fromtimestamp(payload["exp"]),
        }

    def _get_token(self) -> str:
        """
        Fetch a fresh token from Edge if none cached or expired.
        """
        if self._token_cache is None or datetime.now() >= self._token_cache["expire"]:
            logger.debug("Fetching new Microsoft Edge translator token...")
            r = requests.get(self._auth_url, timeout=10)
            r.raise_for_status()
            token = r.text.strip()
            self._token_cache = self._parse_jwt(token)
        return self._token_cache["token"]  # type: ignore[no-any-return]

    def _translate(self, text: str) -> str:
        """
        Translate text using Edge Translator API.
        """
        if not text.strip():
            return text

        params = {
            "to": self._target,
            "api-version": "3.0",
            "includeSentenceLength": "true",
        }
        if self._source.lower() != "auto":
            params["from"] = self._source

        endpoint = f"{self._endpoint}?{urlencode(params)}"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self._get_token()}",
        }
        body = json.dumps([{"text": text.strip()}])

        try:
            r = requests.post(endpoint, headers=headers, data=body, timeout=20)
            if r.status_code == 200:
                data = r.json()
                return data[0]["translations"][0]["text"]  # type: ignore[no-any-return]
            else:
                logger.warning(
                    "HTTP %d during Edge translation: %s",
                    r.status_code,
                    r.text[:120],
                )
                return text
        except Exception as e:
            logger.error("Edge translation failed: %s", e)
            return text
        finally:
            time.sleep(self._sleep)
