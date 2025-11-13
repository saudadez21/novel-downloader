#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.esjzone.client
---------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class EsjzoneClient(CommonClient):
    """
    Specialized client for ESJ Zone novel sites.
    """

    ENCRYPTED_MARKERS = [
        "/assets/img/oops_art.jpg",
        "btn-send-pw",
    ]

    def _dl_check_restricted(self, raw_pages: list[str]) -> bool:
        html = raw_pages[0]
        return all(marker in html for marker in self.ENCRYPTED_MARKERS)
