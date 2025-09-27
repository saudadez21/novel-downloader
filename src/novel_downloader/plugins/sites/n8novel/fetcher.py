#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n8novel.fetcher
----------------------------------------------

"""

import re
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N8novelSession(BaseSession):
    """
    A session class for interacting with the 无限轻小说 (www.8novel.com) novel.
    """

    site_name: str = "n8novel"

    BOOK_INFO_URL = "https://www.8novel.com/novelbooks/{book_id}/"
    CHAPTER_URL = "https://article.8novel.com/read/{book_id}/?{chapter_id}"
    CHAPTER_CONTENT_URL = "https://article.8novel.com/txt/{txt_dir}/{book_id}/{chapter_id}{seed_segment}.html"

    _TXT_DIR_PATTERN = re.compile(r"%2f(\d)%")
    _SPLIT_DIGITS_PATTERN = re.compile(
        r'["\'](\d+(?:,\d+)*)["\']\s*\.split\s*\(\s*["\']\s*,\s*["\']\s*\)', re.DOTALL
    )

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of a single chapter asynchronously.

        Order: [chap_info, content]

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        chapter_html = await self.fetch(url, **kwargs)
        txt_dir = self._extract_txt_dir(chapter_html)
        url_seed = self._extract_url_seed(chapter_html)
        content_url = self._build_chapter_content_url(
            seed=url_seed,
            book_id=book_id,
            chapter_id=chapter_id,
            txt_dir=txt_dir,
        )
        content_html = await self.fetch(content_url, **kwargs)

        return [chapter_html, content_html]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)

    @classmethod
    def _extract_url_seed(cls, html_str: str) -> str:
        """
        From the given HTML/JS source, find all string literals
        of the form "...".split(","), pick the ones that may contain seed,
        and return the last value.
        """
        matches: list[str] = cls._SPLIT_DIGITS_PATTERN.findall(html_str)
        if not matches:
            raise ValueError("No digit lists found in HTML.")
        return matches[-1].split(",")[-1]

    @classmethod
    def _extract_txt_dir(cls, html_str: str) -> str:
        """
        Extract the txt directory number (e.g., '1' or '2') from obfuscated JS.
        """
        match = cls._TXT_DIR_PATTERN.search(html_str)
        if not match:
            raise ValueError("No txt directory number found in HTML.")
        return match.group(1)

    @classmethod
    def _build_chapter_content_url(
        cls,
        seed: str,
        book_id: str,
        chapter_id: str,
        txt_dir: str,
    ) -> str:
        """
        Slices out a 5-character segment of `seed` at offset
        and build content url.
        """
        # Compute start index and slice out 5 chars
        start = (int(chapter_id) * 3) % 100
        seed_segment = seed[start : start + 5]

        return cls.CHAPTER_CONTENT_URL.format(
            book_id=book_id,
            chapter_id=chapter_id,
            seed_segment=seed_segment,
            txt_dir=txt_dir,
        )
