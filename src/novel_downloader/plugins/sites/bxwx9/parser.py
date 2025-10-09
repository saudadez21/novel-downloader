#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.bxwx9.parser
-------------------------------------------

"""

from novel_downloader.plugins.common.parser.biquge1 import Biquge1Parser
from novel_downloader.plugins.registry import registrar


@registrar.register_parser()
class Bxwx9Parser(Biquge1Parser):
    """
    Parser for 笔下文学网 book pages.
    """

    site_name: str = "bxwx9"
