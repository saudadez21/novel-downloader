#!/usr/bin/env python3
"""
novel_downloader.libs.html_builder.core
---------------------------------------
"""

from pathlib import Path

from novel_downloader.infra.paths import (
    HTML_CSS_CHAPTER_PATH,
    HTML_CSS_INDEX_PATH,
    HTML_JS_MAIN_PATH,
)
from novel_downloader.libs.crypto.hash_utils import hash_bytes, hash_file
from novel_downloader.libs.filesystem import sanitize_filename, write_file
from novel_downloader.libs.media.font import detect_font_format
from novel_downloader.libs.media.image import detect_image_format

from .constants import (
    CHAPTER_DIR,
    CSS_DIR,
    FONT_DIR,
    IMAGE_MEDIA_EXTS,
    JS_DIR,
    MEDIA_DIR,
)
from .models import HtmlChapter, HtmlFont, HtmlImage, HtmlVolume, IndexDocument


class HtmlBuilder:
    def __init__(
        self,
        title: str,
        author: str = "",
        description: str = "",
        cover: bytes | None = None,
        subject: list[str] | None = None,
        serial_status: str = "",
        word_count: str = "0",
        language: str = "zh-Hans",
    ) -> None:
        # metadata
        self.title = title
        self.lang = language
        self.cover = cover
        self._cover_filename: str | None = None
        if cover:
            fmt = detect_image_format(cover)
            ext = fmt.lower() if fmt else "jpg"
            self._cover_filename = f"cover.{ext}"

        self._index = IndexDocument(
            title=title,
            author=author,
            description=description,
            subject=subject or [],
            serial_status=serial_status,
            word_count=word_count,
            lang=language,
            cover_filename=self._cover_filename,
        )

        # image state
        self.images: list[HtmlImage] = []
        self._img_map: dict[str, str] = {}
        self._img_idx = 0

        # font state
        self.fonts: list[HtmlFont] = []
        self._font_map: dict[str, HtmlFont] = {}
        self._font_idx = 0

        self._vol_idx = 0

        self._chapters: list[HtmlChapter] = []  # flattened reading order

    def add_image(self, image_path: Path) -> str:
        """
        Add an image resource (deduped by hash) and register it.
        """
        if not (image_path.exists() and image_path.is_file()):
            return ""
        h = hash_file(image_path)
        if h in self._img_map:
            return self._img_map[h]

        data = image_path.read_bytes()
        # Try detecting from magic bytes
        fmt = detect_image_format(data)
        ext = fmt.lower() if fmt else image_path.suffix.lower().lstrip(".") or "bin"

        filename = f"img_{self._img_idx}.{ext}"

        img = HtmlImage(data=data, filename=filename)
        self.images.append(img)
        self._img_map[h] = filename
        self._img_idx += 1
        return filename

    def add_image_bytes(self, data: bytes, mime_type: str = "") -> str:
        """
        Add an image resource from bytes (deduped by hash) and register it.
        """
        if not data:
            return ""

        h = hash_bytes(data)
        if h in self._img_map:
            return self._img_map[h]

        fmt = detect_image_format(data)
        ext = fmt.lower() if fmt else IMAGE_MEDIA_EXTS.get(mime_type, "bin")

        filename = f"img_{self._img_idx}.{ext}"

        img = HtmlImage(data=data, filename=filename)
        self.images.append(img)
        self._img_map[h] = filename
        self._img_idx += 1
        return filename

    def add_font(
        self,
        font_path: Path,
        *,
        family: str | None = None,
        selectors: tuple[str, ...] = (),
    ) -> HtmlFont | None:
        """
        Add a font from a file (deduped by hash) and return a HtmlFont.

        :param font_path: Path to the font file.
        :param family: CSS font-family name to use.
        :param selectors: CSS selectors this font should apply to.
        :return: HtmlFont instance, or None if the path is invalid.
        """
        if not (font_path.exists() and font_path.is_file()):
            return None

        h = hash_file(font_path)
        if h in self._font_map:
            return self._font_map[h]

        data = font_path.read_bytes()
        fmt = detect_font_format(data)
        ext = fmt.lower() if fmt else font_path.suffix.lower().lstrip(".") or "bin"

        family_name = family or f"FontFamily_{self._font_idx}"
        filename = f"font_{self._font_idx}.{ext}"

        font = HtmlFont(
            data=data,
            filename=filename,
            family=family_name,
            selectors=selectors,
        )
        self.fonts.append(font)
        self._font_map[h] = font
        self._font_idx += 1
        return font

    def add_font_bytes(
        self,
        data: bytes,
        *,
        family: str | None = None,
        selectors: tuple[str, ...] = (),
    ) -> HtmlFont | None:
        """
        Add a font from raw bytes (deduped by hash) and return a HtmlFont.

        :param data: Raw font bytes.
        :param family: CSS font-family name to use.
        :param selectors: CSS selectors this font should apply to.
        :return: HtmlFont instance, or None if data is empty.
        """
        if not data:
            return None

        h = hash_bytes(data)
        if h in self._font_map:
            return self._font_map[h]

        fmt = detect_font_format(data)
        ext = fmt.lower() if fmt else "bin"

        family_name = family or f"FontFamily_{self._font_idx}"
        filename = f"font_{self._font_idx}.{ext}"

        font = HtmlFont(
            data=data,
            filename=filename,
            family=family_name,
            selectors=selectors,
        )
        self.fonts.append(font)
        self._font_map[h] = font
        self._font_idx += 1
        return font

    def add_chapter(self, chap: HtmlChapter) -> None:
        """
        Register a single chapter in the global reading order.
        """
        self._chapters.append(chap)
        self._index.add_chapter(chap)

    def add_volume(self, volume: HtmlVolume) -> None:
        """Add a volume and all its chapters to the HTML."""
        self._vol_idx += 1
        self._index.add_volume(volume)

        for chap in volume.chapters:
            self._chapters.append(chap)

    def export(
        self,
        output_path: str | Path,
        *,
        folder: str | None = None,
    ) -> Path:
        """
        Build and export the current book as an HTML folder.

        :param output_path: Path to the parent directory where folder will be created
        :param folder: Optional folder name. If None, use the book title
        """
        return self._build_html(
            output_path=Path(output_path),
            folder=folder,
        )

    def _prepare_output_dir(self, html_dir: Path) -> None:
        css_dir = html_dir / CSS_DIR
        css_dir.mkdir(parents=True, exist_ok=True)
        index_css = HTML_CSS_INDEX_PATH.read_bytes()
        write_file(index_css, css_dir / "index.css")
        chapter_css = HTML_CSS_CHAPTER_PATH.read_bytes()
        write_file(chapter_css, css_dir / "chapter.css")
        js_dir = html_dir / JS_DIR
        js_dir.mkdir(parents=True, exist_ok=True)
        main_js = HTML_JS_MAIN_PATH.read_bytes()
        write_file(main_js, js_dir / "main.js")

    def _write_media(self, html_dir: Path) -> None:
        """
        Write all referenced images and the cover image (if any) into /media.
        """
        media_dir = html_dir / MEDIA_DIR
        # Write chapter images
        if self.images:
            media_dir.mkdir(parents=True, exist_ok=True)
            for img in self.images:
                write_file(img.data, media_dir / img.filename)

        # Write cover image as media/cover.xxx
        if self.cover and self._cover_filename:
            media_dir.mkdir(parents=True, exist_ok=True)
            write_file(self.cover, media_dir / self._cover_filename)

    def _write_fonts(self, html_dir: Path) -> None:
        """
        Write all referenced fonts into /fonts.
        """
        if not self.fonts:
            return

        font_dir = html_dir / FONT_DIR
        font_dir.mkdir(parents=True, exist_ok=True)

        for font in self.fonts:
            write_file(font.data, font_dir / font.filename)

    def _build_index(self, html_dir: Path) -> None:
        index_path = html_dir / "index.html"

        write_file(self._index.to_html(), index_path)

    def _build_chapters(self, html_dir: Path) -> None:
        chap_dir = html_dir / CHAPTER_DIR
        chap_dir.mkdir(parents=True, exist_ok=True)

        if not self._chapters:
            return

        n = len(self._chapters)
        for idx, chap in enumerate(self._chapters):
            prev_link = self._chapters[idx - 1].filename if idx > 0 else ""
            next_link = self._chapters[idx + 1].filename if idx < n - 1 else ""

            chap_html = chap.to_html(
                lang=self.lang,
                prev_link=prev_link,
                next_link=next_link,
            )
            write_file(chap_html, chap_dir / chap.filename)

    def _build_html(self, output_path: Path, folder: str | None) -> Path:
        folder_name = (
            sanitize_filename(folder) if folder else sanitize_filename(self.title)
        )
        html_dir = output_path / folder_name
        self._prepare_output_dir(html_dir)
        self._write_media(html_dir)
        self._write_fonts(html_dir)
        self._build_index(html_dir)
        self._build_chapters(html_dir)
        return html_dir
