#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.qidian_saver.main_saver
----------------------------------------------------

This module implements the `QidianSaver` class, a concrete saver for handling
novel data from Qidian (起点中文网). It defines the logic to compile, structure,
and export novel content in plain text format based on the platform's metadata
and chapter files.
"""

from ..base_saver import BaseSaver
from .qidian_txt import qd_save_as_txt


class QidianSaver(BaseSaver):
    """
    QidianSaver is a platform-specific saver that processes and exports novels
    sourced from Qidian (起点). It extends the BaseSaver interface and provides
    logic for exporting full novels as plain text (.txt) files.
    """

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
        return qd_save_as_txt(self, book_id)
