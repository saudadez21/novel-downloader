#!/usr/bin/env python3
"""
novel_downloader.core.savers.epub_utils.image_loader
----------------------------------------------------

Utilities for embedding image files into an EpubBook.
"""

import logging
from collections.abc import Iterable
from pathlib import Path

from ebooklib import epub

from novel_downloader.utils.constants import EPUB_IMAGE_FOLDER

logger = logging.getLogger(__name__)

_SUPPORTED_IMAGE_MEDIA_TYPES: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}
_DEFAULT_IMAGE_MEDIA_TYPE = "image/jpeg"


def add_images_from_dir(
    book: epub.EpubBook,
    image_dir: str | Path,
) -> epub.EpubBook:
    """
    Load every file in `image_dir` into the EPUB's image folder.

    :param book: The EpubBook object to modify.
    :param image_dir: Path to the directory containing image files.
    :return: The same EpubBook instance, with images added.
    """
    image_dir = Path(image_dir)
    if not image_dir.is_dir():
        logger.warning("Image directory not found or not a directory: %s", image_dir)
        return book

    for img_path in image_dir.iterdir():
        if not img_path.is_file():
            continue

        suffix = img_path.suffix.lower().lstrip(".")
        media_type = _SUPPORTED_IMAGE_MEDIA_TYPES.get(suffix)
        if media_type is None:
            media_type = _DEFAULT_IMAGE_MEDIA_TYPE
            logger.warning(
                "Unknown image suffix '%s' - defaulting media_type to %s",
                suffix,
                media_type,
            )

        try:
            content = img_path.read_bytes()
            item = epub.EpubItem(
                uid=f"img_{img_path.stem}",
                file_name=f"{EPUB_IMAGE_FOLDER}/{img_path.name}",
                media_type=media_type,
                content=content,
            )
            book.add_item(item)
            logger.info("Embedded image: %s", img_path.name)
        except Exception:
            logger.exception("Failed to embed image %s", img_path)

    return book


def add_images_from_dirs(
    book: epub.EpubBook,
    image_dirs: Iterable[str | Path],
) -> epub.EpubBook:
    """
    Add all images from multiple directories into the given EpubBook.

    :param book: The EpubBook object to modify.
    :param image_dirs: An iterable of directory paths to scan for images.
    :return: The same EpubBook instance, with all images added.
    """
    for img_dir in image_dirs:
        book = add_images_from_dir(book, img_dir)
    return book
