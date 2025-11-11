#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mjyhb.parser
-------------------------------------------
"""

from novel_downloader.plugins.common.parser.biquge4 import Biquge4Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class MjyhbParser(Biquge4Parser):
    """
    Parser for 三五中文 book pages.
    """

    site_name: str = "mjyhb"
    BASE_URL = "https://m.mjyhb.com"
