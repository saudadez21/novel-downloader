#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.tasks
---------------------------------------

"""

from dataclasses import dataclass


@dataclass
class CidTask:
    cid: str
    retry: int = 0


@dataclass
class HtmlTask:
    cid: str
    html_list: list[str]
    retry: int = 0
