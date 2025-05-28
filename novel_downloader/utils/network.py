#!/usr/bin/env python3
"""
novel_downloader.utils.network
------------------------------

Utilities for handling HTTP requests and downloading remote resources.
"""

import logging
import random
import time
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

import requests

from .constants import DEFAULT_HEADERS, DEFAULT_IMAGE_SUFFIX
from .file_utils.io import _get_non_conflicting_path, _write_file

logger = logging.getLogger(__name__)

_DEFAULT_CHUNK_SIZE = 8192  # 8KB per chunk for streaming downloads


def http_get_with_retry(
    url: str,
    *,
    retries: int = 3,
    timeout: int = 10,
    backoff: float = 0.5,
    headers: dict[str, str] | None = None,
    stream: bool = False,
) -> requests.Response | None:
    """
    Perform a GET request with retry support.

    :param url: URL to request.
    :param retries: Number of retry attempts.
    :param timeout: Timeout in seconds per request.
    :param backoff: Base backoff delay between retries.
    :param headers: Optional HTTP headers.
    :param stream: Whether to stream the response.
    :return: Response object if successful, else None.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url, timeout=timeout, headers=headers, stream=stream
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning("[http] Attempt %s/%s failed: %s", attempt, retries, e)
            if attempt < retries:
                sleep_time = backoff * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
                time.sleep(sleep_time)
        except Exception as e:
            logger.error("[http] Unexpected error: %s", e)
            break

    logger.error("[http] Failed after %s attempts: %s", retries, url)
    return None


def image_url_to_filename(url: str) -> str:
    """
    Parse and sanitize a image filename from a URL.
    If no filename or suffix exists, fallback to default name and extension.

    :param url: URL string
    :return: Safe filename string
    """
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    filename = Path(path).name

    if not filename:
        filename = "image"

    if not Path(filename).suffix:
        filename += DEFAULT_IMAGE_SUFFIX

    return filename


def download_image(
    url: str,
    target_folder: str | Path | None = None,
    target_name: str | None = None,
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    headers: dict[str, str] | None = None,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
) -> Path | None:
    """
    Download an image from `url` and save it to `target_folder`, returning the Path.
    Can override the filename via `target_name`.

    :param url: Image URL. Can start with 'http', '//', or without protocol.
    :param target_folder: Directory to save into (defaults to cwd).
    :param target_name: Optional filename (with or without extension).
    :param timeout: Request timeout in seconds.
    :param retries: Number of retry attempts.
    :param backoff: Base delay between retries (exponential backoff).
    :param on_exist: What to do if file exists: 'overwrite', 'skip', or 'rename'.
    :return: Path to the saved image, or `None` on any failure.
    """
    # Normalize URL
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith("http"):
        url = "https://" + url

    folder = Path(target_folder) if target_folder else Path.cwd()
    folder.mkdir(parents=True, exist_ok=True)

    if target_name:
        name = target_name
        if not Path(name).suffix:
            # infer ext from URL-derived name
            name += Path(image_url_to_filename(url)).suffix
    else:
        name = image_url_to_filename(url)
    save_path = folder / name

    # Handle existing file
    if save_path.exists():
        if on_exist == "skip":
            logger.debug("Skipping download; file exists: %s", save_path)
            return save_path
        if on_exist == "rename":
            save_path = _get_non_conflicting_path(save_path)

    # Proceed with download
    resp = http_get_with_retry(
        url,
        retries=retries,
        timeout=timeout,
        backoff=backoff,
        headers=headers or DEFAULT_HEADERS,
        stream=False,
    )

    if not (resp and resp.ok):
        logger.warning(
            "Failed to download %s (status=%s)",
            url,
            getattr(resp, "status_code", None),
        )
        return None

    # Write to disk
    try:
        _write_file(
            content=resp.content,
            filepath=save_path,
            mode="wb",
            on_exist=on_exist,
        )
        return save_path
    except Exception:
        logger.exception("Error saving image to %s", save_path)
    return None


def download_font_file(
    url: str,
    target_folder: str | Path,
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    on_exist: Literal["overwrite", "skip", "rename"] = "skip",
) -> Path | None:
    """
    Download a font file from a URL and save it locally with retry and overwrite control

    :param url: Fully-qualified font file URL.
    :param target_folder: Local folder to save the font file.
    :param timeout: Timeout for each request (in seconds).
    :param retries: Number of retry attempts.
    :param backoff: Base backoff time between retries (in seconds).
    :param on_exist: File conflict strategy: 'overwrite', 'skip', or 'rename'.
    :return: Path to the saved font file, or None if failed.
    """
    # Validate and parse URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning("[font] Invalid URL: %s", url)
        return None

    # Determine filename
    filename = Path(unquote(parsed.path)).name
    if not filename:
        logger.warning("[font] Could not extract filename from URL: %s", url)
        return None

    # Resolve save path
    target_folder = Path(target_folder)
    target_folder.mkdir(parents=True, exist_ok=True)
    font_path = target_folder / filename

    # If skip and file exists -> return immediately
    if on_exist == "skip" and font_path.exists():
        logger.debug("[font] File exists, skipping download: %s", font_path)
        return font_path

    # Retry download with exponential backoff
    response = http_get_with_retry(
        url,
        retries=retries,
        timeout=timeout,
        backoff=backoff,
        headers=DEFAULT_HEADERS,
        stream=True,
    )

    if response:
        try:
            if on_exist == "rename":
                font_path = _get_non_conflicting_path(font_path)

            with open(font_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=_DEFAULT_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

            logger.debug("[font] Font saved to: %s", font_path)
            return font_path

        except Exception as e:
            logger.error("[font] Error writing font to disk: %s", e)

    return None


def download_js_file(
    url: str,
    target_folder: str | Path,
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    on_exist: Literal["overwrite", "skip", "rename"] = "skip",
) -> Path | None:
    """
    Download a JavaScript (.js) file from a URL and save it locally.

    :param url: Fully-qualified JS file URL.
    :param target_folder: Local folder to save the JS file.
    :param timeout: Timeout for each request (in seconds).
    :param retries: Number of retry attempts.
    :param backoff: Base backoff time between retries (in seconds).
    :param on_exist: File conflict strategy: 'overwrite', 'skip', or 'rename'.
    :return: Path to the saved JS file, or None if failed.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning("[js] Invalid URL: %s", url)
        return None

    # Determine filename
    filename = Path(unquote(parsed.path)).name
    if not filename.endswith(".js"):
        filename += ".js"

    target_folder = Path(target_folder)
    target_folder.mkdir(parents=True, exist_ok=True)
    save_path = target_folder / filename

    if on_exist == "skip" and save_path.exists():
        logger.debug("[js] File exists, skipping download: %s", save_path)
        return save_path

    response = http_get_with_retry(
        url,
        retries=retries,
        timeout=timeout,
        backoff=backoff,
        headers=DEFAULT_HEADERS,
        stream=False,
    )

    if response and response.ok:
        content = response.content

        if on_exist == "rename":
            save_path = _get_non_conflicting_path(save_path)

        try:
            _write_file(content=content, filepath=save_path, mode="wb")
            logger.debug("[js] JS file saved to: %s", save_path)
            return save_path
        except Exception as e:
            logger.error("[js] Error writing JS to disk: %s", e)

    return None
