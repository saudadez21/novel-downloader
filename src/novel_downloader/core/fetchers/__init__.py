#!/usr/bin/env python3
"""
novel_downloader.core.fetchers
------------------------------

This package provides fetcher implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.

Subpackages:
- biquge (笔趣阁)
- esjzone (ESJ Zone)
- linovelib (哔哩轻小说)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- yamibo (百合会)
- common (通用架构)
"""

from .biquge import (
    BiqugeBrowser,
    BiqugeSession,
)
from .common import (
    CommonBrowser,
    CommonSession,
)
from .esjzone import (
    EsjzoneBrowser,
    EsjzoneSession,
)
from .linovelib import (
    LinovelibBrowser,
    LinovelibSession,
)
from .qianbi import (
    QianbiBrowser,
    QianbiSession,
)
from .qidian import (
    QidianBrowser,
    QidianSession,
)
from .sfacg import (
    SfacgBrowser,
    SfacgSession,
)
from .yamibo import (
    YamiboBrowser,
    YamiboSession,
)

__all__ = [
    "BiqugeBrowser",
    "BiqugeSession",
    "CommonBrowser",
    "CommonSession",
    "EsjzoneBrowser",
    "EsjzoneSession",
    "LinovelibBrowser",
    "LinovelibSession",
    "QianbiBrowser",
    "QianbiSession",
    "QidianBrowser",
    "QidianSession",
    "SfacgBrowser",
    "SfacgSession",
    "YamiboBrowser",
    "YamiboSession",
]
