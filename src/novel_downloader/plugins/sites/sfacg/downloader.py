#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.sfacg.downloader
-----------------------------------------------

"""


from novel_downloader.plugins.common.downloader import CommonDownloader
from novel_downloader.plugins.registry import registrar


@registrar.register_downloader()
class SfacgDownloader(CommonDownloader):
    """
    Specialized Async downloader for sfacg novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return bool(html_list and "本章为VIP章节" in html_list[0])

    def _skip_empty_chapter(self, html_list: list[str]) -> bool:
        return bool(html_list and "/ajax/ashx/common.ashx" in html_list[0])
