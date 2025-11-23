#!/usr/bin/env python3
"""
novel_downloader.infra.sessions
-------------------------------
"""

__all__ = ["create_session"]

from typing import Any

from novel_downloader.schemas import FetcherConfig

from .base import BaseSession


def create_session(
    backend: str,
    cfg: FetcherConfig,
    cookies: dict[str, str] | None = None,
    **kwargs: Any,
) -> BaseSession:
    """
    Factory method to create a session backend instance.

    Available backends:
      * aiohttp
      * httpx
      * curl_cffi
    """
    match backend:
        case "aiohttp":
            from ._aiohttp import AiohttpSession

            return AiohttpSession(cfg, cookies, **kwargs)
        case "httpx":
            from ._httpx import HttpxSession

            return HttpxSession(cfg, cookies, **kwargs)
        case "curl_cffi":
            from ._curl_cffi import CurlCffiSession

            return CurlCffiSession(cfg, cookies, **kwargs)
        case _:
            raise ValueError(f"Unsupported backend: {backend!r}")
