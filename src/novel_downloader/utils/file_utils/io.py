#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils.io
------------------------------------

File I/O utilities for reading and writing data.
"""

__all__ = ["write_file"]

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Literal

from .sanitize import sanitize_filename

logger = logging.getLogger(__name__)

_JSON_INDENT_THRESHOLD = 50 * 1024  # bytes


def _get_non_conflicting_path(path: Path) -> Path:
    """
    If the path exists, generate a new one by appending _1, _2, etc.
    """
    counter = 1
    new_path = path
    while new_path.exists():
        stem = path.stem
        suffix = path.suffix
        new_path = path.with_name(f"{stem}_{counter}{suffix}")
        counter += 1
    return new_path


def write_file(
    content: str | bytes | dict[Any, Any] | list[Any] | Any,
    filepath: str | Path,
    write_mode: str = "w",
    *,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    dump_json: bool = False,
    encoding: str = "utf-8",
) -> Path | None:
    """
    Write content to a file safely with optional atomic behavior
    and JSON serialization.

    :param content: The content to write; can be text, bytes, or a
        JSON-serializable object.
    :param filepath: Destination path (str or Path).
    :param mode: File mode ('w', 'wb'). Auto-determined if None.
    :param on_exist: Behavior if file exists: 'overwrite', 'skip',
        or 'rename'.
    :param dump_json: If True, serialize content as JSON.
    :param encoding: Text encoding for writing.
    :return: Path if writing succeeds, None otherwise.
    """
    path = Path(filepath)
    path = path.with_name(sanitize_filename(path.name))
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        if on_exist == "skip":
            logger.debug("[file] '%s' exists, skipping", path)
            return path
        if on_exist == "rename":
            path = _get_non_conflicting_path(path)
            logger.debug("[file] Renaming target to avoid conflict: %s", path)
        else:
            logger.debug("[file] '%s' exists, will overwrite", path)

    # Prepare content and write mode
    content_to_write: str | bytes
    if dump_json:
        # Serialize original object to JSON string
        json_str = json.dumps(content, ensure_ascii=False, indent=2)
        if len(json_str.encode(encoding)) > _JSON_INDENT_THRESHOLD:
            json_str = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
        content_to_write = json_str
        write_mode = "w"
    else:
        if isinstance(content, (str | bytes)):
            content_to_write = content
        else:
            raise TypeError("Non-JSON content must be str or bytes.")
        write_mode = "wb" if isinstance(content, bytes) else "w"

    try:
        with tempfile.NamedTemporaryFile(
            mode=write_mode,
            encoding=None if "b" in write_mode else encoding,
            newline=None if "b" in write_mode else "\n",
            delete=False,
            dir=path.parent,
        ) as tmp:
            tmp.write(content_to_write)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
        logger.debug("[file] '%s' written successfully", path)
        return path
    except Exception as exc:
        logger.warning("[file] Error writing %r: %s", path, exc)
        return None
