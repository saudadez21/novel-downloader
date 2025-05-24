"""
novel_downloader.core.requesters.sfacg
--------------------------------------

"""

from .async_session import SfacgAsyncSession
from .session import SfacgSession

__all__ = [
    "SfacgAsyncSession",
    "SfacgSession",
]
