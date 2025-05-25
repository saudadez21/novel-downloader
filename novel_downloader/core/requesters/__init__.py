#!/usr/bin/env python3
"""
novel_downloader.core.requesters
--------------------------------

This package provides requester implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.

Subpackages:
- biquge (笔趣阁)
- esjzone (ESJ Zone)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- yamibo (百合会)
- common (通用架构)
"""

from .biquge import (
    BiqugeAsyncSession,
    BiqugeSession,
)
from .common import (
    CommonAsyncSession,
    CommonSession,
)
from .esjzone import (
    EsjzoneAsyncSession,
    EsjzoneSession,
)
from .qianbi import (
    QianbiAsyncSession,
    QianbiSession,
)
from .qidian import (
    QidianBrowser,
    QidianSession,
)
from .sfacg import (
    SfacgAsyncSession,
    SfacgSession,
)
from .yamibo import (
    YamiboAsyncSession,
    YamiboSession,
)

__all__ = [
    "BiqugeAsyncSession",
    "BiqugeSession",
    "CommonAsyncSession",
    "CommonSession",
    "EsjzoneAsyncSession",
    "EsjzoneSession",
    "QianbiAsyncSession",
    "QianbiSession",
    "QidianBrowser",
    "QidianSession",
    "SfacgAsyncSession",
    "SfacgSession",
    "YamiboAsyncSession",
    "YamiboSession",
]
