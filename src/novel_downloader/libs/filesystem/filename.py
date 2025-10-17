#!/usr/bin/env python3
"""
novel_downloader.libs.filesystem.filename
-----------------------------------------
"""

import hashlib
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote, urlparse

DEFAULT_IMAGE_SUFFIX = ".jpg"
ALLOWED_IMAGE_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
}


def url_to_hashed_name(
    url: str,
    *,
    name: str | None = None,
    default_suffix: str = "",
    allowed_suffixes: Iterable[str] | None = None,
) -> str:
    """
    Generate a hashed filename from a URL,
    preserving the file extension if it's in the allowed list.

    :param url: The URL to hash.
    :param name: If set, use this as the filename (without suffix).
    :param default_suffix: The default suffix to use.
    :param allowed_suffixes: An iterable of allowed suffixes.
    """
    parsed = urlparse(url)
    path = Path(unquote(parsed.path))
    suffix = (path.suffix or "").lower()

    if allowed_suffixes and suffix not in allowed_suffixes:
        suffix = default_suffix or ""
    if not suffix and default_suffix:
        suffix = default_suffix

    name = name or hashlib.sha1(url.encode("utf-8")).hexdigest()
    return f"{name}{suffix}"


def img_name(url: str, *, name: str | None = None) -> str:
    """
    Generate a hashed filename for an image URL,
    using a default set of allowed image suffixes.

    :param url: The image URL to hash.
    :param name: Optional explicit name (no suffix).
    """
    return url_to_hashed_name(
        url,
        name=name,
        default_suffix=DEFAULT_IMAGE_SUFFIX,
        allowed_suffixes=ALLOWED_IMAGE_SUFFIXES,
    )
