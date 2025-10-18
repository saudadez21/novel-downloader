#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.esjzone.downloader
-------------------------------------------------

"""


from novel_downloader.plugins.common.downloader import CommonDownloader
from novel_downloader.plugins.registry import registrar


@registrar.register_downloader()
class EsjzoneDownloader(CommonDownloader):
    """
    Specialized Async downloader for ESJ Zone novel sites.
    """

    ENCRYPTED_MARKERS = [
        "/assets/img/oops_art.jpg",
        "btn-send-pw",
    ]

    def _is_access_limited(self, html_list: list[str]) -> bool:
        html = html_list[0]
        return all(marker in html for marker in self.ENCRYPTED_MARKERS)
