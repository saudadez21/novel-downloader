#!/usr/bin/env python3
"""
novel_downloader.core.requesters.biquge.session
-----------------------------------------------

"""

from typing import Any

from novel_downloader.core.requesters.base import BaseSession


class BiqugeSession(BaseSession):
    """
    A session class for interacting with the Biquge (www.b520.cc) novel website.
    """

    BOOK_INFO_URL = "http://www.b520.cc/{book_id}/"
    CHAPTER_URL = "http://www.b520.cc/{book_id}/{chapter_id}.html"

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> str:
        """
        Fetch the raw HTML of the book info page.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        url = self.book_info_url(book_id=book_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(%s) failed: %s",
                book_id,
                exc,
            )
        return ""

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> str:
        """
        Fetch the HTML of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_chapter(%s) failed: %s",
                book_id,
                exc,
            )
        return ""

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
