#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils.normalize
-------------------------------------------

Utilities for normalizing the contents of text files for consistency
across platforms or output formats.

Currently includes line-ending normalization for .txt files.
"""

__all__ = ["normalize_txt_line_endings"]

import logging
from pathlib import Path


def normalize_txt_line_endings(folder_path: str | Path) -> None:
    """
    Convert all .txt files in the given folder (recursively)
    to use Unix-style LF (\\n) line endings.

    :param folder_path: Path to the folder containing .txt files.
                        Can be a str or Path.
    :return: None
    """
    path = Path(folder_path).resolve()
    if not path.exists() or not path.is_dir():
        return

    count_success, count_fail = 0, 0

    for txt_file in path.rglob("*.txt"):
        try:
            content = txt_file.read_text(encoding="utf-8")
            normalized = content.replace("\r\n", "\n").replace("\r", "\n")
            txt_file.write_text(normalized, encoding="utf-8", newline="\n")
            count_success += 1
        except (OSError, UnicodeDecodeError):
            count_fail += 1

    return


if __name__ == "__main__":  # pragma: no cover
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Normalize line endings of .txt files in a folder to LF."
    )
    parser.add_argument(
        "folder", type=str, help="Path to the folder containing .txt files."
    )
    args = parser.parse_args()

    normalize_txt_line_endings(args.folder)
