#!/usr/bin/env python3
"""
novel_downloader.plugins.base.response
--------------------------------------
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterator, Mapping, MutableMapping, Sequence
from typing import Any


class Headers(MutableMapping[str, str]):
    __slots__ = ("_store",)

    def __init__(
        self,
        headers: Mapping[str, str] | Sequence[tuple[str, str]] | None = None,
    ) -> None:
        self._store: dict[str, list[str]] = defaultdict(list)
        if not headers:
            return

        if isinstance(headers, Mapping):
            for k, v in headers.items():
                self.add(k, v)
        else:
            for k, v in headers:
                self.add(k, v)

    def add(self, key: str, value: str | None) -> None:
        self._store[key.lower()].append(value or "")

    def get_all(self, key: str) -> list[str]:
        return self._store.get(key.lower(), [])

    def __getitem__(self, key: str) -> str:
        vals = self._store.get(key.lower())
        if not vals:
            raise KeyError(key)
        return vals[0]

    def __setitem__(self, key: str, value: str) -> None:
        self._store[key.lower()] = [value]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return key.lower() in self._store

    def __repr__(self) -> str:
        items_preview = ", ".join(f"{k}={len(v)}" for k, v in self._store.items())
        return f"<Headers ({items_preview})>"


class BaseResponse:
    """Lightweight internal HTTP-like response used in fetcher."""

    __slots__ = ("content", "headers", "status", "encoding")

    def __init__(
        self,
        *,
        content: bytes,
        headers: Mapping[str, str] | Sequence[tuple[str, str]] | None = None,
        status: int = 200,
        encoding: str = "utf-8",
    ) -> None:
        self.content = content
        self.headers = Headers(headers)
        self.status = status
        self.encoding = encoding

    @property
    def text(self) -> str:
        """Decode content with common fallbacks."""
        encodings = [self.encoding, "gb2312", "gb18030", "gbk", "utf-8"]
        for enc in encodings:
            try:
                return self.content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return self.content.decode(self.encoding, errors="ignore")

    def json(self) -> Any:
        """Parse response text as JSON."""
        return json.loads(self.text)

    @property
    def ok(self) -> bool:
        """Return True if HTTP status code is under 400."""
        return self.status < 400

    def __repr__(self) -> str:
        return f"<BaseResponse status={self.status} len={len(self.content)}>"
