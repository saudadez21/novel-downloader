#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.common_saver.main_saver
----------------------------------------------------

This module implements the `QidianSaver` class, a concrete saver for handling
novel data from Qidian (起点中文网). It defines the logic to compile, structure,
and export novel content in plain text format based on the platform's metadata
and chapter files.
"""

from novel_downloader.config.models import SaverConfig

from ..base_saver import BaseSaver
from .common_txt import common_save_as_txt


class CommonSaver(BaseSaver):
    """
    CommonSaver is a saver that processes and exports novels.
    It extends the BaseSaver interface and provides
    logic for exporting full novels as plain text (.txt) files.
    """

    def __init__(self, config: SaverConfig, site: str):
        """
        Initialize the common saver with site information.

        :param config: A SaverConfig object that defines
                        save paths, formats, and options.
        :param site: Identifier for the site the saver is handling.
        """
        super().__init__(config)
        self._site = site

    def save_as_txt(self, book_id: str) -> None:
        """
        Compile and save a complete novel as a single .txt file.

        Processing steps:
            1. Load book metadata from `book_info.json`, including title,
               author, summary, and chapter structure.
            2. Iterate through all volumes and chapters, appending each
               volume/chapter title and content.
            3. Combine metadata and content into a final formatted text.
            4. Save the final result to the output directory using the
               configured filename template.

        :param book_id: The book identifier (used to locate raw data)
        """
        return common_save_as_txt(self, book_id)

    def save_as_epub(self, book_id: str) -> None:
        """
        Persist the assembled book as a EPUB (.epub) file.

        :param book_id: The book identifier.
        :raises NotImplementedError: If the method is not overridden.
        """
        try:
            from .common_epub import common_save_as_epub
        except ImportError:
            raise NotImplementedError(
                "EPUB export not supported. Please install 'ebooklib'"
            )

        return common_save_as_epub(self, book_id)

    @property
    def site(self) -> str:
        """
        Get the site identifier.

        :return: The site string.
        """
        return self._site

    @site.setter
    def site(self, value: str) -> None:
        """
        Set the site identifier.

        :param value: New site string to set.
        """
        self._site = value
