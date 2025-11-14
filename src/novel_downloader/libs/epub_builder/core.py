#!/usr/bin/env python3
"""
novel_downloader.libs.epub_builder.core
---------------------------------------

Orchestrates the end-to-end EPUB build process by:
  * Managing metadata (title, author, description, language, etc.)
  * Collecting and deduplicating resources (chapters, images, stylesheets, fonts)
  * Registering everything in the OPF manifest and spine
  * Generating nav.xhtml, toc.ncx, content.opf, and the zipped .epub file

Provides:
  * methods to add chapters, volumes, images, and fonts
  * a clean `export()` entry point that writes the final EPUB archive
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED

from novel_downloader.infra.paths import EPUB_CSS_STYLE_PATH
from novel_downloader.libs.crypto.hash_utils import hash_bytes, hash_file
from novel_downloader.libs.media.font import detect_font_format
from novel_downloader.libs.media.image import detect_image_format

from .constants import (
    CONTAINER_TEMPLATE,
    CSS_DIR,
    FONT_DIR,
    FONT_FORMAT_MAP,
    FONT_MEDIA_TYPES,
    IMAGE_DIR,
    IMAGE_MEDIA_TYPES,
    ROOT_PATH,
    TEXT_DIR,
)
from .models import (
    EpubChapter,
    EpubCover,
    EpubFont,
    EpubImage,
    EpubIntro,
    EpubVolume,
    EpubVolumeCover,
    EpubVolumeIntro,
    EpubVolumeIntroDesc,
    EpubVolumeTitle,
    EpubXhtmlFile,
    NavDocument,
    NCXDocument,
    OpfDocument,
)


class EpubBuilder:
    def __init__(
        self,
        title: str,
        author: str = "",
        description: str = "",
        cover_path: Path | None = None,
        subject: list[str] | None = None,
        serial_status: str = "",
        word_count: str = "0",
        uid: str = "",
        language: str = "zh-Hans",
    ) -> None:
        # builder state
        self.items: list[EpubXhtmlFile] = []
        self.images: list[EpubImage] = []
        self.fonts: list[EpubFont] = []

        self._img_map: dict[str, str] = {}
        self._img_idx = 0

        self._font_map: dict[str, EpubFont] = {}
        self._font_idx = 0

        self._vol_idx = 0

        # core EPUB documents
        self.nav = NavDocument(title=title, language=language)
        self.ncx = NCXDocument(title=title, uid=uid)
        self.opf = OpfDocument(
            title=title,
            author=author,
            description=description,
            uid=uid,
            subject=subject or [],
            language=language,
        )

        # register the nav & ncx items
        self.opf.add_manifest_item(
            "nav",
            "nav.xhtml",
            self.nav.media_type,
            properties="nav",
        )
        self.opf.add_manifest_item("ncx", "toc.ncx", self.ncx.media_type)

        # register the css
        self.opf.add_manifest_item(
            id="style",
            href=f"{CSS_DIR}/style.css",
            media_type="text/css",
        )

        self._init_cover(cover_path)

        intro = EpubIntro(
            id="intro",
            filename="intro.xhtml",
            title="书籍简介",
            book_title=title,
            author=author,
            description=description,
            subject=subject or [],
            serial_status=serial_status,
            word_count=word_count,
        )
        self.items.append(intro)
        self.opf.add_manifest_item(
            intro.id,
            f"{TEXT_DIR}/{intro.filename}",
            intro.media_type,
        )
        self.opf.add_spine_item(intro.id)
        self.nav.add_chapter(intro.id, intro.title, f"{TEXT_DIR}/{intro.filename}")
        self.ncx.add_chapter(intro.id, intro.title, f"{TEXT_DIR}/{intro.filename}")

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

        mtype = IMAGE_MEDIA_TYPES.get(ext)
        if not mtype:
            return ""

        res_id = f"img_{self._img_idx}"
        filename = f"{res_id}.{ext}"

        img = EpubImage(id=res_id, data=data, media_type=mtype, filename=filename)
        self.images.append(img)
        self.opf.add_manifest_item(
            img.id,
            f"{IMAGE_DIR}/{img.filename}",
            img.media_type,
        )

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

        ext = detect_image_format(data)
        mtype = IMAGE_MEDIA_TYPES.get(ext) if ext else None

        # Fallback to provided mime_type
        if not mtype and mime_type:
            for k, v in IMAGE_MEDIA_TYPES.items():
                if v == mime_type:
                    ext, mtype = k, v
                    break

        if not (ext and mtype):
            return ""

        res_id = f"img_{self._img_idx}"
        filename = f"{res_id}.{ext}"

        img = EpubImage(
            id=res_id,
            data=data,
            media_type=mtype,
            filename=filename,
        )
        self.images.append(img)
        self.opf.add_manifest_item(
            img.id,
            f"{IMAGE_DIR}/{img.filename}",
            img.media_type,
        )

        self._img_map[h] = filename
        self._img_idx += 1
        return filename

    def add_font(
        self,
        font_path: Path,
        *,
        family: str | None = None,
        selectors: tuple[str, ...] = (),
    ) -> EpubFont | None:
        """
        Add a font from a file (deduped by hash) and register it in the manifest.

        :param font_path: Path to the font file.
        :param family: CSS font-family name. If None, a unique name is generated.
        :param selectors: CSS selectors this font should apply to in chapters.
        :return: EpubFont instance, or None if invalid/unsupported.
        """
        if not (font_path.exists() and font_path.is_file()):
            return None

        h = hash_file(font_path)
        if h in self._font_map:
            return self._font_map[h]

        data = font_path.read_bytes()
        fmt = detect_font_format(data)
        ext = fmt.lower() if fmt else font_path.suffix.lower().lstrip(".") or "bin"

        media_type = FONT_MEDIA_TYPES.get(ext)
        if not media_type:
            return None

        res_id = f"font_{self._font_idx}"
        family_name = family or f"FontFamily_{self._font_idx}"
        filename = f"{res_id}.{ext}"
        format = FONT_FORMAT_MAP.get(ext, "truetype")

        font = EpubFont(
            id=res_id,
            filename=filename,
            media_type=media_type,
            format=format,
            data=data,
            family=family_name,
            selectors=selectors,
        )
        self.fonts.append(font)
        self.opf.add_manifest_item(
            font.id,
            f"{FONT_DIR}/{font.filename}",
            font.media_type,
        )
        self._font_map[h] = font
        self._font_idx += 1
        return font

    def add_font_bytes(
        self,
        data: bytes,
        *,
        family: str | None = None,
        selectors: tuple[str, ...] = (),
    ) -> EpubFont | None:
        """
        Add a font from raw bytes (deduped by hash) and register it.

        :param data: Raw font bytes.
        :param family: CSS font-family name. If None, a unique name is generated.
        :param selectors: CSS selectors this font should apply to in chapters.
        :return: EpubFont instance, or None if invalid/unsupported.
        """
        if not data:
            return None

        h = hash_bytes(data)
        if h in self._font_map:
            return self._font_map[h]

        fmt = detect_font_format(data)
        ext = fmt.lower() if fmt else "bin"

        media_type = FONT_MEDIA_TYPES.get(ext)
        if not media_type:
            return None

        res_id = f"font_{self._font_idx}"
        family_name = family or f"FontFamily_{self._font_idx}"
        filename = f"{res_id}.{ext}"
        format = FONT_FORMAT_MAP.get(ext, "truetype")

        font = EpubFont(
            id=res_id,
            filename=filename,
            media_type=media_type,
            format=format,
            data=data,
            family=family_name,
            selectors=selectors,
        )
        self.fonts.append(font)
        self.opf.add_manifest_item(
            font.id,
            f"{FONT_DIR}/{font.filename}",
            font.media_type,
        )
        self._font_map[h] = font
        self._font_idx += 1
        return font

    def add_chapter(self, chap: EpubChapter) -> None:
        self.items.append(chap)
        self.opf.add_manifest_item(
            chap.id,
            f"{TEXT_DIR}/{chap.filename}",
            chap.media_type,
        )
        self.opf.add_spine_item(chap.id)
        self.nav.add_chapter(chap.id, chap.title, f"{TEXT_DIR}/{chap.filename}")
        self.ncx.add_chapter(chap.id, chap.title, f"{TEXT_DIR}/{chap.filename}")

    def add_volume(self, volume: EpubVolume) -> None:
        """Add a volume cover, intro, and all its chapters to the EPUB."""
        vol_id = f"vol_{self._vol_idx}"
        self._vol_idx += 1

        cover_filename: str = ""
        if volume.cover_path:
            cover_filename = self.add_image(volume.cover_path)

        if cover_filename:
            vol_cover: EpubVolumeCover | EpubVolumeTitle = EpubVolumeCover(
                id=f"{vol_id}-cover",
                filename=f"{vol_id}_cover.xhtml",
                title=volume.title,
                image_name=cover_filename,
            )
        else:
            vol_cover = EpubVolumeTitle(
                id=f"{vol_id}-title",
                filename=f"{vol_id}_title.xhtml",
                full_title=volume.title,
            )

        self.items.append(vol_cover)
        self.opf.add_manifest_item(
            vol_cover.id,
            f"{TEXT_DIR}/{vol_cover.filename}",
            vol_cover.media_type,
        )
        self.opf.add_spine_item(vol_cover.id)

        if volume.intro:
            if cover_filename:
                vol_intro: EpubVolumeIntro | EpubVolumeIntroDesc = EpubVolumeIntro(
                    id=f"{vol_id}-intro",
                    filename=f"{vol_id}_intro.xhtml",
                    title=volume.title,
                    description=volume.intro,
                )
            else:
                vol_intro = EpubVolumeIntroDesc(
                    id=f"{vol_id}-intro",
                    filename=f"{vol_id}_intro.xhtml",
                    title=volume.title,
                    description=volume.intro,
                )
            self.items.append(vol_intro)
            self.opf.add_manifest_item(
                vol_intro.id,
                f"{TEXT_DIR}/{vol_intro.filename}",
                vol_intro.media_type,
            )
            self.opf.add_spine_item(vol_intro.id)

        # nested chapters
        entries: list[tuple[str, str, str]] = []
        for chap in volume.chapters:
            self.items.append(chap)
            self.opf.add_manifest_item(
                chap.id,
                f"{TEXT_DIR}/{chap.filename}",
                chap.media_type,
            )
            self.opf.add_spine_item(chap.id)
            entries.append((chap.id, chap.title, f"{TEXT_DIR}/{chap.filename}"))

        # TOC updates
        self.ncx.add_volume(
            id=vol_cover.id,
            label=volume.title,
            src=f"{TEXT_DIR}/{vol_cover.filename}",
            chapters=entries,
        )
        self.nav.add_volume(
            id=vol_cover.id,
            label=volume.title,
            src=f"{TEXT_DIR}/{vol_cover.filename}",
            chapters=entries,
        )

    def export(self, output_path: str | Path) -> Path:
        """
        Build and export the current book as an EPUB file.

        :param output_path: Path to save the final .epub file.
        """
        return self._build_epub(output_path=Path(output_path))

    def _init_cover(self, cover_path: Path | None) -> None:
        if not cover_path or not cover_path.is_file():
            return

        data = cover_path.read_bytes()
        # Try detecting from magic bytes
        fmt = detect_image_format(data)
        ext = fmt.lower() if fmt else cover_path.suffix.lower().lstrip(".")

        mtype = IMAGE_MEDIA_TYPES.get(ext)
        if not mtype:
            return

        cover_img = EpubImage(
            id="cover-img",
            data=data,
            media_type=mtype,
            filename=f"cover.{ext}",
        )
        self.images.append(cover_img)
        self.opf.add_manifest_item(
            cover_img.id,
            f"{IMAGE_DIR}/{cover_img.filename}",
            cover_img.media_type,
            properties="cover-image",
        )

        cover_item = EpubCover(ext=ext)
        self.items.append(cover_item)
        self.opf.add_manifest_item(
            cover_item.id,
            f"{TEXT_DIR}/{cover_item.filename}",
            cover_item.media_type,
        )
        self.opf.add_spine_item(cover_item.id)
        self.nav.add_chapter(
            cover_item.id,
            cover_item.title,
            f"{TEXT_DIR}/{cover_item.filename}",
        )
        self.ncx.add_chapter(
            cover_item.id,
            cover_item.title,
            f"{TEXT_DIR}/{cover_item.filename}",
        )

    def _build_epub(self, output_path: Path) -> Path:
        """
        Write out the .epub ZIP file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w") as epub:
            # must be first and uncompressed
            epub.writestr(
                "mimetype",
                "application/epub+zip",
                compress_type=ZIP_STORED,
            )

            # container.xml
            epub.writestr(
                "META-INF/container.xml",
                CONTAINER_TEMPLATE,
                compress_type=ZIP_DEFLATED,
            )

            # core documents
            epub.writestr(
                f"{ROOT_PATH}/nav.xhtml",
                self.nav.to_xhtml(),
                compress_type=ZIP_DEFLATED,
            )
            epub.writestr(
                f"{ROOT_PATH}/toc.ncx",
                self.ncx.to_xml(),
                compress_type=ZIP_DEFLATED,
            )
            epub.writestr(
                f"{ROOT_PATH}/content.opf",
                self.opf.to_xml(),
                compress_type=ZIP_DEFLATED,
            )

            # stylesheets
            style_text = EPUB_CSS_STYLE_PATH.read_text("utf-8")
            path = f"{ROOT_PATH}/{CSS_DIR}/style.css"
            epub.writestr(path, style_text, compress_type=ZIP_DEFLATED)

            # items
            for item in self.items:
                path = f"{ROOT_PATH}/{TEXT_DIR}/{item.filename}"
                epub.writestr(path, item.to_xhtml(), compress_type=ZIP_DEFLATED)

            # images
            for img in self.images:
                path = f"{ROOT_PATH}/{IMAGE_DIR}/{img.filename}"
                epub.writestr(path, img.data, compress_type=ZIP_DEFLATED)

            # fonts
            for font in self.fonts:
                path = f"{ROOT_PATH}/{FONT_DIR}/{font.filename}"
                epub.writestr(path, font.data, compress_type=ZIP_DEFLATED)

        return output_path
