#!/usr/bin/env python3
"""
novel_downloader.core.requesters.linovelib.session
--------------------------------------------------

"""

import re
from typing import Any

from novel_downloader.core.requesters.base import BaseSession
from novel_downloader.utils.time_utils import sleep_with_random_delay


class LinovelibSession(BaseSession):
    """
    A session class for interacting with the
    linovelib (www.linovelib.com) novel website.
    """

    BASE_URL = "https://www.linovelib.com"
    BOOK_INFO_URL = "https://www.linovelib.com/novel/{book_id}.html"
    BOOK_VOL_URL = "https://www.linovelib.com/novel/{book_id}/{vol_id}.html"
    CHAPTER_URL = "https://www.linovelib.com/novel/{book_id}/{chapter_id}.html"

    _VOL_ID_PATTERN: re.Pattern[str] = re.compile(r"/novel/\d+/(vol_\d+)\.html")

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page.

        :param book_id: The book identifier.
        :return: A list of HTML strings: [info_html, vol1_html, ..., volN_html]
        """
        url = self.book_info_url(book_id=book_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            info_html = resp.text

            vol_ids = self._extract_vol_ids(info_html)
            vol_ids.reverse()

            vol_htmls = []
            for vol_id in vol_ids:
                sleep_with_random_delay(self._request_interval)
                html = self.get_book_volume(book_id, vol_id, **kwargs)
                if html:
                    vol_htmls.append(html)

            return [info_html] + vol_htmls
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(%s) failed: %s",
                book_id,
                exc,
            )
        return []

    def get_book_volume(
        self,
        book_id: str,
        vol_id: str,
        **kwargs: Any,
    ) -> str:
        """
        Fetch the HTML content of a specific volume.

        :param book_id: The book identifier.
        :param vol_id: The volume identifier.
        :return: The volume content as a string.
        """
        url = self.volume_url(book_id=book_id, vol_id=vol_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_volume(%s, %s) failed: %s",
                book_id,
                vol_id,
                exc,
            )
        return ""

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the HTML pages of a chapter (may span multiple sub-pages).

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: A list of HTML strings from page 1 to N.
        """
        html_pages: list[str] = []
        idx = 1

        while True:
            # 构建分页 URL
            chapter_suffix = chapter_id if idx == 1 else f"{chapter_id}_{idx}"
            relative_path = self.relative_chapter_url(
                book_id=book_id,
                chapter_id=chapter_suffix,
            )
            if idx > 1 and relative_path not in html_pages[-1]:
                break
            full_url = self.BASE_URL + relative_path

            try:
                resp = self.get(full_url, **kwargs)
                resp.raise_for_status()
                html_pages.append(resp.text)
                idx += 1

                sleep_with_random_delay(self._request_interval)

            except Exception as exc:
                self.logger.warning(
                    "[session] get_book_chapter(%s page %d) failed: %s",
                    chapter_id,
                    idx,
                    exc,
                )
                break

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
    def volume_url(cls, book_id: str, vol_id: str) -> str:
        """
        Construct the URL for fetching a specific volume.

        :param book_id: The identifier of the book.
        :param vol_id: The identifier of the volume.
        :return: Fully qualified volume URL.
        """
        return cls.BOOK_VOL_URL.format(book_id=book_id, vol_id=vol_id)

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
    def relative_chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Return the relative URL path for a given chapter.
        """
        return f"/novel/{book_id}/{chapter_id}.html"

    def _extract_vol_ids(self, html_str: str) -> list[str]:
        """
        Extract volume IDs (like 'vol_12345') from the info HTML.

        :param html_str: Raw HTML of the info page.
        :return: List of volume ID strings.
        """
        # /novel/{book_id}/{vol_id}.html
        return self._VOL_ID_PATTERN.findall(html_str)
