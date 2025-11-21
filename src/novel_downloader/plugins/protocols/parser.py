#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.parser
-----------------------------------------

Protocol defining the interface for parsing book metadata and chapter content.

A parser is responsible for extracting structured data from the raw
HTML or JSON returned by a :class:`FetcherProtocol`.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from novel_downloader.schemas import BookInfoDict, ChapterDict

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray
    from paddleocr import TextRecognition


class ParserProtocol(Protocol):
    """
    Protocol for a site-specific parser implementation.

    A parser transforms raw HTML or JSON data fetched from a site into
    structured Python dictionaries suitable for downstream processing.
    """

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse book-level metadata from raw HTML, JSON, or text responses.

        Usually called with the result of
        :meth:`FetcherProtocol.fetch_book_info`.

        :param raw_pages: Raw page contents for the book info section.
        :return: Parsed :class:`BookInfoDict`, or ``None`` if parsing fails.
        """
        ...

    def parse_chapter_content(
        self,
        raw_pages: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a chapter's data from raw HTML, JSON, or text responses.

        Usually called with the result of
        :meth:`FetcherProtocol.fetch_chapter_content`.

        :param raw_pages: Raw page contents for the chapter.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Parsed :class:`ChapterDict`, or ``None`` if parsing fails.
        """
        ...


class _ParserContext(ParserProtocol, Protocol):
    """
    Internal protocol used for mixin typing.

    Provides common attributes and helper methods shared between
    concrete parser classes and mixins.
    """

    site_name: str
    _enable_ocr: bool
    _batch_size: int
    _use_truncation: bool
    _remove_watermark: bool
    _cut_mode: str
    _cache_dir: Path

    @property
    def ocr_model(self) -> "TextRecognition":
        ...

    def _is_ad_line(self, line: str) -> bool:
        """
        Check if a line contains any ad text.

        :param line: Single text line.
        :return: True if line matches ad pattern, else False.
        """
        ...

    @classmethod
    def _norm_space(cls, s: str, c: str = " ") -> str:
        """
        collapse any run of whitespace (incl. newlines, full-width spaces)

        :param s: Input string to normalize.
        :param c: Replacement character to use for collapsed whitespace.
        """
        ...

    @staticmethod
    def _first_str(xs: list[str], replaces: list[tuple[str, str]] | None = None) -> str:
        ...

    @staticmethod
    def _join_strs(xs: list[str], replaces: list[tuple[str, str]] | None = None) -> str:
        ...

    def _extract_text_from_image(
        self,
        images: "list[NDArray[np.uint8]]",
        batch_size: int = 1,
    ) -> list[tuple[str, float]]:
        """
        Perform OCR on a list of images and extract recognized text.

        :param images: A list of image arrays (np.ndarray) to be processed by OCR.
        :param batch_size: Number of images to process per inference batch (minimum 1).
        :return: A list of tuples in the form (text, confidence_score).
        """
        ...
