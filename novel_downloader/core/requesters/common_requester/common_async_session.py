#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.common_requester.common_async_session
----------------------------------------------------------------------

This module defines a `CommonAsyncSession` class for handling HTTP requests
to common novel sites **asynchronously**. It provides methods to retrieve
raw book info pages and chapter contents using a flexible URL templating
system defined by a site profile, with retry logic and random delays.
"""

import asyncio
import random
from typing import Dict, Optional

from novel_downloader.config import RequesterConfig, SiteProfile
from novel_downloader.core.requesters.base_async_session import BaseAsyncSession


class CommonAsyncSession(BaseAsyncSession):
    """
    A common async session for handling site-specific HTTP requests.

    :ivar _site: The unique identifier or name of the site.
    :ivar _profile: Metadata and URL templates related to the site.
    """

    def __init__(
        self,
        config: RequesterConfig,
        site: str,
        profile: SiteProfile,
        cookies: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize a CommonAsyncSession instance.

        :param config: The RequesterConfig instance containing settings.
        :param site: The identifier or domain of the target site.
        :param profile: The site's metadata and URL templates.
        :param cookies: Optional cookies to preload into the session.
        """
        self._init_session(config=config, cookies=cookies)
        self._site = site
        self._profile = profile

    async def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Relies on BaseAsyncSession.fetch for retry logic, then sleeps with jitter.

        :param book_id:   The book identifier.
        :param wait_time: Base seconds to sleep (with 0.5-1.5x random factor).
        :return:          The page content as a string.
        """
        url = self.book_info_url.format(book_id=book_id)
        html = await self.fetch(url)
        base = wait_time if wait_time is not None else self._config.wait_time
        await asyncio.sleep(base * random.uniform(0.5, 1.5))
        return html

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the raw HTML of a single chapter asynchronously.

        Relies on BaseAsyncSession.fetch for retry logic, then sleeps with jitter.

        :param book_id:    The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time:  Base seconds to sleep (with 0.5-1.5x random factor).
        :return:           The chapter content as a string.
        """
        url = self.chapter_url.format(book_id=book_id, chapter_id=chapter_id)
        html = await self.fetch(url)
        base = wait_time if wait_time is not None else self._config.wait_time
        await asyncio.sleep(base * random.uniform(0.5, 1.5))
        return html

    @property
    def site(self) -> str:
        """Return the site name."""
        return self._site

    @property
    def book_info_url(self) -> str:
        """Return the URL template for fetching book info."""
        return self._profile["book_info_url"]

    @property
    def chapter_url(self) -> str:
        """Return the URL template for fetching chapter content."""
        return self._profile["chapter_url"]
