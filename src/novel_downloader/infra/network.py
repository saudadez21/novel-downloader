#!/usr/bin/env python3
"""
novel_downloader.infra.network
------------------------------

Utilities for handling HTTP requests and downloading remote resources.
"""

__all__ = ["download"]

from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from novel_downloader.infra.http_defaults import DEFAULT_HEADERS
from novel_downloader.libs.filesystem import sanitize_filename, write_file


def _normalize_url(url: str) -> str:
    """
    Ensure URL has scheme, defaulting to https:// if missing.
    """
    if url.startswith("//"):
        return "https:" + url
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def _new_session(
    retries: int,
    backoff: float,
    headers: dict[str, str] | None,
) -> requests.Session:
    session = requests.Session()
    session.headers.update(headers or DEFAULT_HEADERS)
    if retries <= 0:
        return session

    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[413, 429, 500, 502, 503, 504],
        allowed_methods={"GET", "HEAD", "OPTIONS"},
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def download(
    url: str,
    target_dir: str | Path | None = None,
    filename: str | None = None,
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    headers: dict[str, str] | None = None,
    on_exist: Literal["overwrite", "skip"] = "overwrite",
) -> Path | None:
    """
    Download a URL to disk, with retries, optional skip, and cleanup on failure.

    :param url: the file URL.
    :param target_dir: directory to save into.
    :param filename: override the basename (else from URL path).
    :param timeout: per-request timeout.
    :param retries: GET retry count.
    :param backoff: exponential backoff base.
    :param headers: optional headers.
    :param on_exist: if 'skip', return filepath
    :return: path to the downloaded file.
    """
    url = _normalize_url(url)

    folder = Path(target_dir) if target_dir else Path.cwd()
    folder.mkdir(parents=True, exist_ok=True)

    # Determine final save path
    if filename:
        save_path = folder / sanitize_filename(filename)
    else:
        parsed_url = urlparse(url)
        url_path = Path(unquote(parsed_url.path))
        name = sanitize_filename(url_path.name or "unnamed")
        save_path = folder / name

    # Handle existing file
    if save_path.exists() and on_exist == "skip":
        return save_path

    with _new_session(retries, backoff, headers) as session:
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()

            # Write to disk
            return write_file(
                content=resp.content,
                filepath=save_path,
                on_exist=on_exist,
            )
        except Exception:
            return None

    return None
