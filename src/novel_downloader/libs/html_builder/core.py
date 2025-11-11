#!/usr/bin/env python3
"""
novel_downloader.libs.html_builder.core
---------------------------------------
"""

from html import escape
from pathlib import Path

from novel_downloader.infra.paths import (
    HTML_CSS_CHAPTER_PATH,
    HTML_CSS_INDEX_PATH,
    HTML_JS_MAIN_PATH,
)
from novel_downloader.libs.crypto.hash_utils import hash_bytes, hash_file
from novel_downloader.libs.filesystem import sanitize_filename, write_file
from novel_downloader.libs.media.image import detect_image_format

from .constants import (
    CHAPTER_DIR,
    CSS_DIR,
    IMAGE_MEDIA_EXTS,
    INDEX_TEMPLATE,
    JS_DIR,
    MEDIA_DIR,
)
from .models import HtmlChapter, HtmlImage, HtmlVolume


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
        self.author = author
        self.description = description
        self.cover = cover
        self.subject = subject or []
        self.serial_status = serial_status
        self.word_count = word_count
        self.lang = language

        self._cover_filename: str | None = None

        # builder state
        self.images: list[HtmlImage] = []
        self._img_map: dict[str, str] = {}
        self._img_idx = 0
        self._vol_idx = 0

        self.volumes: list[HtmlVolume] = []
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
        ext = fmt.lower() if fmt else image_path.suffix.lower().lstrip(".")

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

    def add_chapter(self, chap: HtmlChapter) -> None:
        """
        Register a single chapter in the global reading order.
        """
        self._chapters.append(chap)

    def add_volume(self, volume: HtmlVolume) -> None:
        """Add a volume and all its chapters to the HTML."""
        self._vol_idx += 1
        self.volumes.append(volume)

        for chap in volume.chapters:
            self.add_chapter(chap)

    def export(self, output_path: str | Path) -> Path:
        """
        Build and export the current book as an EPUB file.

        :param output_path: Path to save the final .epub file.
        """
        return self._build_html(output_path=Path(output_path))

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
        if self.cover:
            media_dir.mkdir(parents=True, exist_ok=True)
            fmt = detect_image_format(self.cover)
            ext = fmt.lower() if fmt else "jpg"
            cover_name = f"cover.{ext}"
            write_file(self.cover, media_dir / cover_name)
            self._cover_filename = cover_name

    def _build_index(self, html_dir: Path) -> None:
        index_path = html_dir / "index.html"

        # --- Header ---
        header_parts: list[str] = []

        header_parts.append(f"<h1>{escape(self.title)}</h1>")

        if self.author:
            header_parts.append(f'<p class="author">作者：{escape(self.author)}</p>')

        if self._cover_filename:
            header_parts.append(
                f'<img src="{MEDIA_DIR}/{self._cover_filename}" '
                f'alt="封面" class="cover">'
            )

        meta_parts: list[str] = []

        if self.serial_status:
            meta_parts.append(f"状态：{escape(self.serial_status)}")
        if self.word_count:
            meta_parts.append(f"字数：{escape(str(self.word_count))}")
        if meta_parts:
            header_parts.append(f'<p class="meta">{"　".join(meta_parts)}</p>')

        if self.subject:
            tags_str = " / ".join(escape(tag) for tag in self.subject)
            header_parts.append(f'<p class="tags">标签：{tags_str}</p>')

        if self.description:
            header_parts.append(
                f'<p class="description">{escape(self.description)}</p>'
            )

        header_html = "\n    ".join(header_parts)

        # --- TOC grouped by volume ---
        toc_blocks: list[str] = []
        for vol in self.volumes:
            vol_parts: list[str] = []
            vol_parts.append(
                f'<section class="volume">\n' f"  <h3>{escape(vol.title)}</h3>"
            )

            if vol.intro:
                vol_parts.append(f'  <p class="volume-intro">{escape(vol.intro)}</p>')

            if vol.chapters:
                vol_parts.append("  <ul>")
                for chap in vol.chapters:
                    href = f"{CHAPTER_DIR}/{chap.filename}"
                    vol_parts.append(
                        f'    <li><a href="{href}">{escape(chap.title)}</a></li>'
                    )
                vol_parts.append("  </ul>")

            vol_parts.append("</section>")
            toc_blocks.append("\n".join(vol_parts))

        toc_html = "\n\n".join(toc_blocks)

        # --- Render template ---
        index_html = INDEX_TEMPLATE.format(
            lang=self.lang,
            book_name=escape(self.title),
            header=header_html,
            toc_html=toc_html,
        )

        write_file(index_html, index_path)

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

    def _build_html(self, output_path: Path) -> Path:
        html_dir = output_path / sanitize_filename(self.title)
        self._prepare_output_dir(html_dir)
        self._write_media(html_dir)
        self._build_index(html_dir)
        self._build_chapters(html_dir)
        return html_dir
