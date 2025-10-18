#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yibige.downloader
------------------------------------------------

"""


from novel_downloader.plugins.common.downloader import CommonDownloader
from novel_downloader.plugins.registry import registrar


@registrar.register_downloader()
class YibigeDownloader(CommonDownloader):
    """
    Specialized Async downloader for yibige novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "<b>Parse error</b>" in html_list[0]
