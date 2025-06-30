#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils.io
------------------------------------

File I/O utilities for reading and writing text, JSON, and binary data.

Includes:
- Safe, atomic file saving with optional overwrite and auto-renaming
- JSON pretty-printing with size-aware formatting
- Simple helpers for reading files with fallback and logging
"""

import json
import logging
import tempfile
from importlib.resources import files
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


def _write_file(
    content: str | bytes | dict[Any, Any] | list[Any] | Any,
    filepath: str | Path,
    mode: str | None = None,
    *,
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    dump_json: bool = False,
    encoding: str = "utf-8",
) -> bool:
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
    :return: True if writing succeeds, False otherwise.
    """
    path = Path(filepath)
    path = path.with_name(sanitize_filename(path.name))
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        if on_exist == "skip":
            logger.debug("[file] '%s' exists, skipping", path)
            return False
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
        return True
    except Exception as exc:
        logger.warning("[file] Error writing %r: %s", path, exc)
        return False


def save_as_txt(
    content: str,
    filepath: str | Path,
    *,
    encoding: str = "utf-8",
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
) -> bool:
    """
    Save plain text content to the given file path.

    :param content: Text content to write.
    :param filepath: Destination file path.
    :param encoding: Text encoding to use (default: 'utf-8').
    :param on_exist: How to handle existing files: 'overwrite', 'skip', or 'rename'.
    :return: True if successful, False otherwise.
    """
    return _write_file(
        content=content,
        filepath=filepath,
        mode="w",
        on_exist=on_exist,
        dump_json=False,
        encoding=encoding,
    )


def save_as_json(
    content: Any,
    filepath: str | Path,
    *,
    encoding: str = "utf-8",
    on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
) -> bool:
    """
    Save JSON-serializable content to the given file path.

    :param content: Data to write as JSON.
    :param filepath: Destination file path.
    :param encoding: Text encoding to use (default: 'utf-8').
    :param on_exist: How to handle existing files: 'overwrite', 'skip', or 'rename'.
    :return: True if successful, False otherwise.
    """
    return _write_file(
        content=content,
        filepath=filepath,
        mode="w",
        on_exist=on_exist,
        dump_json=True,
        encoding=encoding,
    )


def read_text_file(filepath: str | Path, encoding: str = "utf-8") -> str | None:
    """
    Read a UTF-8 text file.

    :param filepath: Path to file.
    :param encoding: Encoding to use.
    :return: Text content or None on failure.
    """
    path = Path(filepath)
    try:
        return path.read_text(encoding=encoding)
    except Exception as e:
        logger.warning("[file] Failed to read %r: %s", path, e)
        return None


def read_json_file(filepath: str | Path, encoding: str = "utf-8") -> Any | None:
    """
    Read a JSON file and parse it into Python objects.

    :param filepath: Path to file.
    :param encoding: Encoding to use.
    :return: Python object or None on failure.
    """
    path = Path(filepath)
    try:
        return json.loads(path.read_text(encoding=encoding))
    except Exception as e:
        logger.warning("[file] Failed to read %r: %s", path, e)
        return None


def read_binary_file(filepath: str | Path) -> bytes | None:
    """
    Read a binary file and return its content as bytes.

    :param filepath: Path to file.
    :return: Bytes or None on failure.
    """
    path = Path(filepath)
    try:
        return path.read_bytes()
    except Exception as e:
        logger.warning("[file] Failed to read %r: %s", path, e)
        return None


def load_text_resource(
    filename: str,
    package: str = "novel_downloader.resources.text",
) -> str:
    """
    Load and return the contents of a text resource.

    :param filename: Name of the text file (e.g. "blacklist.txt").
    :param package: Package path where resources live (default: text resources).
                    For other resource types, point to the appropriate subpackage
                    (e.g. "novel_downloader.resources.css").
    :return: File contents as a string.
    """
    resource_path = files(package).joinpath(filename)
    return resource_path.read_text(encoding="utf-8")


def load_blacklisted_words() -> set[str]:
    """
    Convenience loader for the blacklist.txt in the text resources.

    :return: A set of non-empty, stripped lines from blacklist.txt.
    """
    text = load_text_resource("blacklist.txt")
    return {line.strip() for line in text.splitlines() if line.strip()}


__all__ = [
    "save_as_txt",
    "save_as_json",
    "read_text_file",
    "read_json_file",
    "read_binary_file",
    "load_text_resource",
    "load_blacklisted_words",
]
