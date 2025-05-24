"""
novel_downloader.core.requesters.qianbi.session
-----------------------------------------------

"""

from typing import Any

from novel_downloader.core.requesters.base import BaseSession


class QianbiSession(BaseSession):
    """
    A session class for interacting with the
    Qianbi (www.23qb.com) novel website.
    """

    BASE_URLS = [
        "www.23qb.com",
        "www.23qb.net",
    ]

    BOOK_INFO_URL = "https://www.23qb.com/book/{book_id}/"
    BOOK_CATALOG_URL = "https://www.23qb.com/book/{book_id}/catalog"
    CHAPTER_URL = "https://www.23qb.com/book/{book_id}/{chapter_id}.html"

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info and catalog pages.

        Order: [info, catalog]

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        info_url = self.book_info_url(book_id=book_id)
        catalog_url = self.book_catalog_url(book_id=book_id)

        pages = []
        try:
            resp = self.get(info_url, **kwargs)
            resp.raise_for_status()
            pages.append(resp.text)
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(info:%s) failed: %s",
                book_id,
                exc,
            )
            pages.append("")

        try:
            resp = self.get(catalog_url, **kwargs)
            resp.raise_for_status()
            pages.append(resp.text)
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(catalog:%s) failed: %s",
                book_id,
                exc,
            )
            pages.append("")

        return pages

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
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
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_chapter(%s) failed: %s",
                book_id,
                exc,
            )
        return []

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def book_catalog_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's catalog page.

        :param book_id: The identifier of the book.
        :return: Fully qualified catalog page URL.
        """
        return cls.BOOK_CATALOG_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
