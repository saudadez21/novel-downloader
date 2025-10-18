#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.b520.downloader
----------------------------------------------

"""


from novel_downloader.plugins.common.downloader import CommonDownloader
from novel_downloader.plugins.registry import registrar


@registrar.register_downloader()
class B520Downloader(CommonDownloader):
    """
    Specialized Async downloader for b520 novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "<h1>Bad GateWay</h1>" in html_list[0]
