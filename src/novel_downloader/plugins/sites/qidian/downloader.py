#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.downloader
------------------------------------------------

Downloader implementation for Qidian novels,
with handling for restricted and encrypted chapters
"""

import asyncio

from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.common.downloader import DualBatchDownloader
from novel_downloader.plugins.protocols import FetcherProtocol, ParserProtocol
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict, DownloaderConfig


@registrar.register_downloader()
class QidianDownloader(DualBatchDownloader):
    """
    Specialized downloader for Qidian (起点) novels.

    Processes each chapter in a single worker that
    handles fetch -> parse -> enqueue storage.
    """

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        super().__init__(fetcher, parser, config, site)
        self._request_interval = max(1.0, config.request_interval)

    @property
    def workers(self) -> int:
        return 1

    @staticmethod
    def _check_restricted(html_list: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. not subscribed/purchased).

        :param html_list: Raw HTML string.
        """
        if not html_list:
            return True
        markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
        return any(m in html_list[0] for m in markers)

    @staticmethod
    def _check_encrypted(html_list: list[str]) -> bool:
        if not html_list:
            return True
        return '"cES":2' in html_list[0]

    def _need_refetch(self, chap: ChapterDict) -> bool:
        return bool(chap.get("extra", {}).get("encrypted", False))

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
    ) -> ChapterDict | None:
        """
        Fetch, debug-save, parse a single chapter with retries.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self._retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                if self._check_restricted(html_list):
                    self.logger.info(
                        "qidian: restricted chapter content (book=%s, chapter=%s)",
                        book_id,
                        cid,
                    )
                    return None
                encrypted = self._check_encrypted(html_list)

                folder = "html_encrypted" if encrypted else "html_plain"
                self._save_html_pages(book_id, cid, html_list, folder=folder)

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if encrypted and not chap:
                    self.logger.info(
                        "qidian: failed to parse encrypted chapter (book=%s, chapter=%s)",  # noqa: E501
                        book_id,
                        cid,
                    )
                    return None
                if not chap:
                    raise ValueError("Empty parse result")
                return chap

            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info(
                        "qidian: retrying chapter (book=%s, chapter=%s, attempt=%s): %s",  # noqa: E501
                        book_id,
                        cid,
                        attempt + 1,
                        e,
                    )
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff,
                        mul_spread=1.2,
                        max_sleep=backoff + 3,
                    )
                else:
                    self.logger.warning(
                        "qidian: failed chapter (book=%s, chapter=%s): %s",
                        book_id,
                        cid,
                        e,
                    )
        return None
