#!/usr/bin/env python3
"""
novel_downloader.core.requesters.common.session
-----------------------------------------------

This module defines a `CommonSession` class for handling HTTP requests
to common novel sites. It provides methods to retrieve raw book
information pages and chapter contents using a flexible URL templating
system defined by a site profile.
"""

from typing import Any

from novel_downloader.config import RequesterConfig, SiteProfile
from novel_downloader.core.requesters.base import BaseSession


class CommonSession(BaseSession):
    """
    A common session for handling site-specific HTTP requests.
    """

    def __init__(
        self,
        config: RequesterConfig,
        site: str,
        profile: SiteProfile,
        cookies: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize a CommonSession instance.

        :param config: The RequesterConfig instance containing settings.
        :param site: The identifier or domain of the target site.
        :param profile: The site's metadata and URL templates.
        :param cookies: Optional cookies to preload into the session.
        """
        super().__init__(config, cookies)
        self._site = site
        self._profile = profile

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        url = self.book_info_url(book_id=book_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as e:
            self.logger.warning("Failed to fetch book info for %s: %s", book_id, e)
        return []

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as e:
            self.logger.warning(
                "Failed to fetch book chapter for %s(%s): %s",
                book_id,
                chapter_id,
                e,
            )
        return []

    @property
    def site(self) -> str:
        """Return the site name."""
        return self._site

    def book_info_url(self, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return self._profile["book_info_url"].format(book_id=book_id)

    def chapter_url(self, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return self._profile["chapter_url"].format(
            book_id=book_id, chapter_id=chapter_id
        )
