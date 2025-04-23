#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces.saver_protocol
------------------------------------------------

Defines the SaverProtocol interface for persisting completed books in
TXT, EPUB, Markdown, and PDF formats.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SaverProtocol(Protocol):
    """
    A saver must implement a method to persist a completed book as plain text.

    It may also optionally implement an EPUB (or other format) saver.
    """

    def save_as_txt(self, book_id: str) -> None:
        """
        Persist the assembled book as a .txt file.

        :param book_id: The book identifier (used for filename or lookup).
        """
        ...

    def save_as_epub(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as an .epub file.

        :param book_id: The book identifier.
        """
        ...

    def save_as_md(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a Markdown (.md) file.

        :param book_id: The book identifier.
        """
        ...

    def save_as_pdf(self, book_id: str) -> None:
        """
        Optional: Persist the assembled book as a PDF file.

        :param book_id: The book identifier.
        """
        ...
