#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shencou.downloader
-------------------------------------------------

"""


from novel_downloader.plugins.common.downloader import CommonDownloader
from novel_downloader.plugins.registry import registrar


@registrar.register_downloader()
class ShencouDownloader(CommonDownloader):
    """
    Specialized Async downloader for shencou novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "404错误，页面不存在，或文章已删除" in html_list[0]
