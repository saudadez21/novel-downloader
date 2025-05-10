#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.network
------------------------------

Utilities for handling HTTP requests and downloading remote resources.
"""

import logging
import random
import time
from pathlib import Path
from typing import Dict, Literal, Optional, Union
from urllib.parse import unquote, urlparse

import requests

from .constants import DEFAULT_HEADERS, DEFAULT_IMAGE_SUFFIX
from .file_utils.io import _get_non_conflicting_path, _write_file, read_binary_file

logger = logging.getLogger(__name__)

_DEFAULT_CHUNK_SIZE = 8192  # 8KB per chunk for streaming downloads


def http_get_with_retry(
    url: str,
    *,
    retries: int = 3,
    timeout: int = 10,
    backoff: float = 0.5,
    headers: Optional[Dict[str, str]] = None,
    stream: bool = False,
) -> Optional[requests.Response]:
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


def download_image_as_bytes(
    url: str,
    target_folder: Optional[Union[str, Path]] = None,
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
) -> Optional[bytes]:
    """
    Download an image from a given URL and return its content as bytes.

    If on_exist='skip' and the file already exists, it will be read from disk
    instead of being downloaded again.

    :param url: Image URL. Can start with 'http', '//', or without protocol.
    :param target_folder: Optional folder to save the image (str or Path).
    :param timeout: Request timeout in seconds.
    :param retries: Number of retry attempts.
    :param backoff: Base delay between retries (exponential backoff).
    :param on_exist: What to do if file exists: 'overwrite', 'skip', or 'rename'.
    :return: Image content as bytes, or None if failed.
    """
    # Normalize URL
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith("http"):
        url = "https://" + url

    save_path = None
    if target_folder:
        target_folder = Path(target_folder)
        filename = image_url_to_filename(url)
        save_path = target_folder / filename

        if on_exist == "skip" and save_path.exists():
            logger.info(
                "[image] '%s' exists, skipping download and reading from disk.",
                save_path,
            )
            return read_binary_file(save_path)

    # Proceed with download
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

        if save_path:
            _write_file(
                content=content,
                filepath=save_path,
                mode="wb",
                on_exist=on_exist,
            )

        return content

    return None


def download_font_file(
    url: str,
    target_folder: Union[str, Path],
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    on_exist: Literal["overwrite", "skip", "rename"] = "skip",
) -> Optional[Path]:
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
        logger.info("[font] File exists, skipping download: %s", font_path)
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

            logger.info("[font] Font saved to: %s", font_path)
            return font_path

        except Exception as e:
            logger.error("[font] Error writing font to disk: %s", e)

    return None


def download_js_file(
    url: str,
    target_folder: Union[str, Path],
    *,
    timeout: int = 10,
    retries: int = 3,
    backoff: float = 0.5,
    on_exist: Literal["overwrite", "skip", "rename"] = "skip",
) -> Optional[Path]:
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
        logger.info("[js] File exists, skipping download: %s", save_path)
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
            logger.info("[js] JS file saved to: %s", save_path)
            return save_path
        except Exception as e:
            logger.error("[js] Error writing JS to disk: %s", e)

    return None
