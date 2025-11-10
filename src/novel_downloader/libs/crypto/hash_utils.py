#!/usr/bin/env python3
"""
novel_downloader.libs.crypto.hash_utils
---------------------------------------
"""

import hashlib
from pathlib import Path


def hash_file(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 hash of a file.

    :param file_path: The Path object of the file to hash.
    :param chunk_size: The chunk size to read the file (default: 8192).
    :return: The SHA256 hash string (lowercase hex) of the file content.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    """
    Compute the SHA256 hash of a bytes object.

    :param data: Bytes to hash.
    :return: The SHA256 hash string (lowercase hex) of the data.
    """
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()
