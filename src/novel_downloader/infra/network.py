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
from novel_downloader.libs.filesystem import sanitize_filename
from novel_downloader.libs.filesystem.file import _unique_path, write_file


def _normalize_url(url: str) -> str:
    """
    Ensure URL has scheme, defaulting to https:// if missing.
    """
    if url.startswith("//"):
        return "https:" + url
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def _build_filepath(
    url: str,
    folder: Path,
    filename: str | None,
    default_suffix: str,
    on_exist: Literal["overwrite", "skip", "rename"],
) -> Path:
    parsed_url = urlparse(url)
    url_path = Path(unquote(parsed_url.path))

    raw_name = filename or url_path.name or "unnamed"
    name = sanitize_filename(raw_name)

    if "." not in name and (url_path.suffix or default_suffix):
        name += url_path.suffix or default_suffix

    file_path = folder / name
    if on_exist == "rename":
        file_path = _unique_path(file_path)

    return file_path


def _new_session(
    retries: int,
    backoff: float,
    headers: dict[str, str] | None,
) -> requests.Session:
    session = requests.Session()
    session.headers.update(headers or DEFAULT_HEADERS)

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
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    default_suffix: str = "",
) -> Path | None:
    """
    Download a URL to disk, with retries, optional rename/skip, and cleanup on failure.

    :param url: the file URL.
    :param target_dir: directory to save into.
    :param filename: override the basename (else from URL path).
    :param timeout: per-request timeout.
    :param retries: GET retry count.
    :param backoff: exponential backoff base.
    :param headers: optional headers.
    :param on_exist: if 'skip', return filepath; if 'rename', auto-rename.
    :param default_suffix: used if no suffix in URL or filename.
    :return: path to the downloaded file.
    """
    url = _normalize_url(url)

    folder = Path(target_dir) if target_dir else Path.cwd()
    folder.mkdir(parents=True, exist_ok=True)

    save_path = _build_filepath(
        url,
        folder,
        filename,
        default_suffix,
        on_exist,
    )

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
