#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.common_requester.common_session
------------------------------------------------------------------

This module defines a `CommonSession` class for handling HTTP requests
to common novel sites. It provides methods to retrieve raw book
information pages and chapter contents using a flexible URL templating
system defined by a site profile.
"""

from typing import Dict, Optional

from novel_downloader.config import RequesterConfig, SiteProfile
from novel_downloader.utils.time_utils import sleep_with_random_delay

from ..base_session import BaseSession


class CommonSession(BaseSession):
    """
    A common session for handling site-specific HTTP requests.

    :ivar _site: The unique identifier or name of the site.
    :ivar _profile: Metadata and URL templates related to the site.
    :ivar session: The HTTP session used to make requests.
    """

    def __init__(
        self,
        config: RequesterConfig,
        site: str,
        profile: SiteProfile,
        cookies: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a CommonSession instance.

        :param config: The RequesterConfig instance containing settings.
        :param site: The identifier or domain of the target site.
        :param profile: The site's metadata and URL templates.
        :param cookies: Optional cookies to preload into the session.
        """
        self._init_session(config=config, cookies=cookies)
        self._site = site
        self._profile = profile

    def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML (or JSON) of the book info page.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        :raises requests.HTTPError: If the request returns an unsuccessful status code.
        """
        url = self.book_info_url.format(book_id=book_id)
        response = self.session.get(url)
        response.raise_for_status()
        content = response.text
        base = wait_time if wait_time is not None else self._config.wait_time
        sleep_with_random_delay(base)
        return content

    def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the raw HTML (or JSON) of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        :raises requests.HTTPError: If the request returns an unsuccessful status code.
        """
        url = self.chapter_url.format(book_id=book_id, chapter_id=chapter_id)
        response = self.session.get(url)
        response.raise_for_status()
        content = response.text
        base = wait_time if wait_time is not None else self._config.wait_time
        sleep_with_random_delay(base)
        return content

    @property
    def site(self) -> str:
        """Return the site name."""
        return self._site

    @property
    def book_info_url(self) -> str:
        """
        Return the URL template for fetching book information.
        """
        return self._profile["book_info_url"]

    @property
    def chapter_url(self) -> str:
        """
        Return the URL template for fetching chapter information.
        """
        return self._profile["chapter_url"]
