"""
novel_downloader.core.requesters.esjzone
----------------------------------------

"""

from .async_session import EsjzoneAsyncSession
from .session import EsjzoneSession

__all__ = [
    "EsjzoneAsyncSession",
    "EsjzoneSession",
]
