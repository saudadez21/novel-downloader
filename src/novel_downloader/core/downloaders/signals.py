#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.signals
-----------------------------------------

Utilities for signaling task termination and reporting async progress.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Final, final


@final
class StopToken:
    """Typed sentinel used to end queues."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "STOP"


STOP: Final[StopToken] = StopToken()

# from typing_extensions import TypeIs
# def is_stop(x: object) -> TypeIs[StopToken]:
#     """Type guard so `if is_stop(item)` narrows type to StopToken."""
#     return isinstance(x, StopToken)


class Progress:
    """Lightweight progress reporter."""

    __slots__ = ("done", "total", "hook")

    def __init__(self, total: int, hook: Callable[[int, int], Awaitable[None]] | None):
        self.done = 0
        self.total = total
        self.hook = hook

    async def bump(self, n: int = 1) -> None:
        self.done += n
        if self.hook:
            await self.hook(self.done, self.total)
