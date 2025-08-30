#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.eightnovel
-----------------------------------------

"""

import re
from re import Pattern
from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig


@register_fetcher(
    site_keys=["8novel", "eightnovel"],
)
class EightnovelSession(BaseSession):
    """
    A session class for interacting with the 无限轻小说 (www.8novel.com) novel website.
    """

    BOOK_INFO_URL = "https://www.8novel.com/novelbooks/{book_id}/"
    CHAPTER_URL = "https://article.8novel.com/read/{book_id}/?{chapter_id}"
    CHAPTER_CONTENT_URL = (
        "https://article.8novel.com/txt/1/{book_id}/{chapter_id}{seed_segment}.html"
    )

    _SPLIT_STR_PATTERN = re.compile(
        r'["\']([^"\']+)["\']\s*\.split\s*\(\s*["\']\s*,\s*["\']\s*\)', re.DOTALL
    )
    _DIGIT_LIST_PATTERN: Pattern[str] = re.compile(r"^\d+(?:,\d+)*$")

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("eightnovel", config, cookies, **kwargs)

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
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
        url_seed = self._extract_url_seed(chapter_html)
        content_url = self._build_chapter_content_url(
            seed=url_seed,
            book_id=book_id,
            chapter_id=chapter_id,
        )
        content_html = await self.fetch(content_url, **kwargs)

        return [chapter_html, content_html]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
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
        split_literals: list[str] = cls._SPLIT_STR_PATTERN.findall(html_str)

        numeric_lists = [
            lit for lit in split_literals if cls._DIGIT_LIST_PATTERN.fullmatch(lit)
        ]

        if not numeric_lists:
            return ""

        last_list = numeric_lists[-1]
        return last_list.split(",")[-1]

    @classmethod
    def _build_chapter_content_url(
        cls, seed: str, book_id: str, chapter_id: str
    ) -> str:
        """
        Slices out a 5-character segment of `seed` at offset
        and build content url.
        """
        # Compute start index and slice out 5 chars
        start = (int(chapter_id) * 3) % 100
        seed_segment = seed[start : start + 5]

        return cls.CHAPTER_CONTENT_URL.format(
            book_id=book_id, chapter_id=chapter_id, seed_segment=seed_segment
        )
