#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.deqixs.fetcher
------------------------------------------------

"""

from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession


class DeqixsSession(BaseSession):
    """
    A session class for interacting with the 得奇小说网 (www.deqixs.com) novel.
    """

    BASE_URL = "https://www.deqixs.com"
    BOOK_INFO_URL = "https://www.deqixs.com/xiaoshuo/{book_id}/"
    CHAPTER_URL = "https://www.deqixs.com/xiaoshuo/{book_id}/{chapter_id}.html"

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
        html_pages: list[str] = []
        idx = 1

        while True:
            chapter_suffix = chapter_id if idx == 1 else f"{chapter_id}-{idx}"
            relative_path = f"/xiaoshuo/{book_id}/{chapter_suffix}.html"
            full_url = self.BASE_URL + relative_path

            if idx > 1 and relative_path not in html_pages[-1]:
                break

            try:
                html = await self.fetch(full_url, **kwargs)
            except Exception as exc:
                self.logger.warning(
                    "deqixs get_book_chapter(%s page %d) failed: %s",
                    chapter_id,
                    idx,
                    exc,
                )
                break

            html_pages.append(html)
            idx += 1
            await self._sleep()

        return html_pages

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
