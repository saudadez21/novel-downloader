#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquguo.parser
---------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge1 import Biquge1Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class BiquguoParser(Biquge1Parser):
    """
    Parser for 笔趣阁小说网 book pages.
    """

    site_name: str = "biquguo"
