#!/usr/bin/env python3
"""
novel_downloader.models.tasks
-----------------------------

"""

from dataclasses import dataclass


@dataclass
class CidTask:
    prev_cid: str | None
    cid: str
    retry: int = 0


@dataclass
class HtmlTask:
    cid: str
    retry: int
    html_list: list[str]
