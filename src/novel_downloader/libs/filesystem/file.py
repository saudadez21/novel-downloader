#!/usr/bin/env python3
"""
novel_downloader.libs.filesystem.file
-------------------------------------

File I/O utilities for reading and writing data.
"""

__all__ = ["write_file"]

import tempfile
from pathlib import Path
from typing import Literal

from .sanitize import sanitize_filename


def _unique_path(path: Path, max_tries: int = 100) -> Path:
    """
    Return a unique file path by appending _1, _2, ... if needed.

    Falls back to a UUID suffix if all attempts fail.
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix

    for counter in range(1, max_tries + 1):
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate

    # fallback: append a random/unique suffix
    import uuid

    return path.with_name(f"{stem}_{uuid.uuid4().hex}{suffix}")


def write_file(
    content: str | bytes,
    filepath: Path,
    *,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    encoding: str = "utf-8",
) -> Path:
    """
    Write content to a file safely with atomic replacement.

    :param content: The content to write; can be text or bytes.
    :param filepath: Destination path.
    :param on_exist: Behavior if file exists.
    :param encoding: Text encoding for writing.
    :return: The final path where the content was written.
    :raise: Any I/O error such as PermissionError or OSError
    """
    filepath = filepath.with_name(sanitize_filename(filepath.name))
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if filepath.exists():
        match on_exist:
            case "skip":
                return filepath
            case "rename":
                filepath = _unique_path(filepath)

    write_mode = "wb" if isinstance(content, bytes) else "w"

    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode=write_mode,
            encoding=None if "b" in write_mode else encoding,
            newline=None if "b" in write_mode else "\n",
            delete=False,
            dir=filepath.parent,
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        tmp_path.replace(filepath)
        return filepath
    except Exception:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
