#!/usr/bin/env python3
"""
novel_downloader.core.fetchers
------------------------------

This package provides fetcher implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.
"""

__all__ = [
    "get_fetcher",
    "BiqugeSession",
    "EsjzoneSession",
    "LinovelibSession",
    "PiaotiaSession",
    "QianbiSession",
    "QidianSession",
    "SfacgSession",
    "TtkanSession",
    "YamiboSession",
]

from .biquge import BiqugeSession
from .esjzone import EsjzoneSession
from .linovelib import LinovelibSession
from .piaotia import PiaotiaSession
from .qianbi import QianbiSession
from .qidian import QidianSession
from .registry import get_fetcher
from .sfacg import SfacgSession
from .ttkan import TtkanSession
from .yamibo import YamiboSession
