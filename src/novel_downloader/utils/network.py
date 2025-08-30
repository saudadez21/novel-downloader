#!/usr/bin/env python3
"""
novel_downloader.utils.network
------------------------------

Utilities for handling HTTP requests and downloading remote resources.
"""

__all__ = ["download"]

import logging
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import DEFAULT_HEADERS
from .file_utils import sanitize_filename
from .file_utils.io import _get_non_conflicting_path, write_file

logger = logging.getLogger(__name__)
_DEFAULT_CHUNK_SIZE = 8192  # 8KB per chunk for streaming downloads


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
    folder: Path,
    url: str,
    filename: str | None,
    default_suffix: str,
    on_exist: Literal["overwrite", "skip", "rename"],
) -> Path:
    parsed_url = urlparse(url)
    url_path = Path(unquote(parsed_url.path))

    raw_name = filename or url_path.name or "unnamed"
    name = sanitize_filename(raw_name)
    suffix = default_suffix or url_path.suffix
    if suffix and not suffix.startswith("."):
        suffix = "." + suffix

    file_path = folder / name
    if not file_path.suffix and suffix:
        file_path = file_path.with_suffix(suffix)

    if on_exist == "rename":
        file_path = _get_non_conflicting_path(file_path)
    return file_path


def _make_session(
    retries: int,
    backoff: float,
    headers: dict[str, str] | None,
) -> requests.Session:
    session = requests.Session()
    session.headers.update(headers or DEFAULT_HEADERS)

    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
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
    stream: bool = False,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    default_suffix: str = "",
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
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
    :param stream: Whether to stream the response.
    :param on_exist: if 'skip', return filepath; if 'rename', auto-rename.
    :param default_suffix: used if no suffix in URL or filename.
    :param chunk_size: streaming chunk size.
    :return: path to the downloaded file.
    """
    url = _normalize_url(url)

    folder = Path(target_dir) if target_dir else Path.cwd()
    folder.mkdir(parents=True, exist_ok=True)

    save_path = _build_filepath(
        folder,
        url,
        filename,
        default_suffix,
        on_exist,
    )

    # Handle existing file
    if save_path.exists() and on_exist == "skip":
        logger.debug("Skipping download; file exists: %s", save_path)
        return save_path

    with _make_session(retries, backoff, headers) as session:
        try:
            resp = session.get(url, timeout=timeout, stream=stream)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("[download] request failed: %s", e)
            return None

        # Write to disk
        if stream:
            try:
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                return save_path
            except Exception as e:
                logger.warning("[download] write failed: %s", e)
                save_path.unlink(missing_ok=True)
                return None
        else:
            return write_file(
                content=resp.content,
                filepath=save_path,
                write_mode="wb",
                on_exist=on_exist,
            )
    return None
