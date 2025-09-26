#!/usr/bin/env python3
"""
novel_downloader.libs.epub.builder
----------------------------------

Orchestrates the end-to-end EPUB build process by:
  * Managing metadata (title, author, description, language, etc.)
  * Collecting and deduplicating resources (chapters, images, stylesheets)
  * Registering everything in the OPF manifest and spine
  * Generating nav.xhtml, toc.ncx, content.opf, and the zipped .epub file

Provides:
  * methods to add chapters, volumes, images, and styles
  * a clean `export()` entry point that writes the final EPUB archive
"""

import zipfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED

from novel_downloader.infra.paths import (
    CSS_INTRO_PATH,
    VOLUME_BORDER_IMAGE_PATH,
)

from .constants import (
    COVER_IMAGE_TEMPLATE,
    CSS_FOLDER,
    IMAGE_FOLDER,
    IMAGE_MEDIA_TYPES,
    ROOT_PATH,
    TEXT_FOLDER,
)
from .documents import (
    NavDocument,
    NCXDocument,
    OpfDocument,
)
from .models import (
    Chapter,
    ChapterEntry,
    EpubResource,
    ImageResource,
    StyleSheet,
    Volume,
)
from .utils import (
    build_book_intro,
    build_container_xml,
    build_volume_intro,
    hash_file,
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
    ):
        # metadata
        self.title = title
        self.author = author
        self.description = description
        self.language = language
        self.subject = subject or []
        self.serial_status = serial_status
        self.word_count = word_count
        self.uid = uid

        # builder state
        self.chapters: list[Chapter] = []
        self.images: list[ImageResource] = []
        self.styles: list[StyleSheet] = []
        self._img_map: dict[str, str] = {}
        self._img_idx = 0
        self._vol_idx = 0

        # core EPUB documents
        self.nav = NavDocument(title=title, language=language)
        self.ncx = NCXDocument(title=title, uid=uid)
        self.opf = OpfDocument(
            title=title,
            author=author,
            description=description,
            uid=uid,
            subject=self.subject,
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

        self._init_styles()
        self._init_cover(cover_path)
        self._init_intro()

    def add_image(self, image_path: Path) -> str:
        """
        Add an image resource (deduped by hash) and register it.
        """
        if not (image_path.exists() and image_path.is_file()):
            return ""
        h = hash_file(image_path)
        if h in self._img_map:
            return self._img_map[h]

        ext = image_path.suffix.lower().lstrip(".")
        mtype = IMAGE_MEDIA_TYPES.get(ext)
        if not mtype:
            return ""

        res_id = f"img_{self._img_idx}"
        filename = f"{res_id}.{ext}"
        data = image_path.read_bytes()
        img = ImageResource(id=res_id, data=data, media_type=mtype, filename=filename)
        self.images.append(img)
        self._register(img, folder=IMAGE_FOLDER, in_spine=False)

        self._img_map[h] = filename
        self._img_idx += 1
        return filename

    def add_chapter(self, chap: Chapter) -> None:
        self.chapters.append(chap)
        self._register(chap, folder=TEXT_FOLDER)
        self.nav.add_chapter(chap.id, chap.title, f"{TEXT_FOLDER}/{chap.filename}")
        self.ncx.add_chapter(chap.id, chap.title, f"{TEXT_FOLDER}/{chap.filename}")

    def add_volume(self, volume: Volume) -> None:
        """Add a volume cover, intro, and all its chapters to the EPUB."""
        # volume-specific cover
        if volume.cover:
            filename = self.add_image(volume.cover)
            cover_html = f'<img class="width100" src="../{IMAGE_FOLDER}/{filename}"/>'
            cover_chap = Chapter(
                id=f"vol_{self._vol_idx}_cover",
                title=volume.title,
                content=cover_html,
                filename=f"vol_{self._vol_idx}_cover.xhtml",
            )
            self.chapters.append(cover_chap)
            self._register(
                cover_chap,
                folder=TEXT_FOLDER,
                properties="duokan-page-fullscreen",
            )

        # volume intro page
        intro_content = build_volume_intro(volume.title, volume.intro)
        vol_intro = Chapter(
            id=f"vol_{self._vol_idx}",
            title=volume.title,
            content=intro_content,
            css=[self.intro_css],
            filename=f"vol_{self._vol_idx}.xhtml",
        )
        self.chapters.append(vol_intro)
        self._register(vol_intro, folder=TEXT_FOLDER)

        # nested chapters
        entries: list[ChapterEntry] = []
        for chap in volume.chapters:
            self.chapters.append(chap)
            self._register(chap, folder=TEXT_FOLDER)
            entries.append(
                ChapterEntry(
                    id=chap.id,
                    label=chap.title,
                    src=f"{TEXT_FOLDER}/{chap.filename}",
                )
            )

        # TOC updates
        self.ncx.add_volume(
            id=f"vol_{self._vol_idx}",
            label=volume.title,
            src=f"{TEXT_FOLDER}/{vol_intro.filename}",
            chapters=entries,
        )
        self.nav.add_volume(
            id=f"vol_{self._vol_idx}",
            label=volume.title,
            src=f"{TEXT_FOLDER}/{vol_intro.filename}",
            chapters=entries,
        )

        self._vol_idx += 1

    def add_stylesheet(self, css: StyleSheet) -> None:
        """
        Register an external CSS file in the EPUB.
        """
        self.styles.append(css)
        self._register(css, folder=CSS_FOLDER, in_spine=False)

    def export(self, output_path: str | Path) -> Path:
        """
        Build and export the current book as an EPUB file.

        :param output_path: Path to save the final .epub file.
        """
        return self._build_epub(output_path=Path(output_path))

    def _register(
        self,
        res: EpubResource,
        folder: str,
        in_spine: bool = True,
        properties: str | None = None,
    ) -> None:
        """
        Add resource to the manifest—and optionally to the spine.
        """
        href = f"{folder}/{res.filename}"
        self.opf.add_manifest_item(res.id, href, res.media_type, properties)
        if in_spine:
            self.opf.add_spine_item(res.id, properties)

    def _init_styles(self) -> None:
        # volume border & intro CSS
        self.intro_css = StyleSheet(
            id="intro_style",
            content=CSS_INTRO_PATH.read_text("utf-8"),
            filename="intro_style.css",
        )
        self.styles.append(self.intro_css)
        self._register(self.intro_css, folder=CSS_FOLDER, in_spine=False)

        try:
            border_bytes = VOLUME_BORDER_IMAGE_PATH.read_bytes()
        except FileNotFoundError:
            return
        border = ImageResource(
            id="img-volume-border",
            data=border_bytes,
            media_type="image/png",
            filename="volume_border.png",
        )
        self.images.append(border)
        self._register(border, folder=IMAGE_FOLDER, in_spine=False)

    def _init_cover(self, cover_path: Path | None) -> None:
        if not cover_path or not cover_path.is_file():
            return
        ext = cover_path.suffix.lower().lstrip(".")
        mtype = IMAGE_MEDIA_TYPES.get(ext)
        if not mtype:
            return

        data = cover_path.read_bytes()
        cover_img = ImageResource(
            id="cover-img",
            data=data,
            media_type=mtype,
            filename=f"cover.{ext}",
        )
        self.images.append(cover_img)
        self._register(
            cover_img,
            folder=IMAGE_FOLDER,
            in_spine=False,
            properties="cover-image",
        )

        cover_chapter = Chapter(
            id="cover",
            title="Cover",
            content=COVER_IMAGE_TEMPLATE.format(ext=ext),
            filename="cover.xhtml",
        )
        self.chapters.append(cover_chapter)
        self._register(
            cover_chapter,
            folder=TEXT_FOLDER,
            properties="duokan-page-fullscreen",
        )
        self.nav.add_chapter(
            cover_chapter.id,
            cover_chapter.title,
            f"{TEXT_FOLDER}/{cover_chapter.filename}",
        )
        self.ncx.add_chapter(
            cover_chapter.id,
            cover_chapter.title,
            f"{TEXT_FOLDER}/{cover_chapter.filename}",
        )
        self.opf.include_cover = True

    def _init_intro(self) -> None:
        intro_html = build_book_intro(
            book_name=self.title,
            author=self.author,
            serial_status=self.serial_status,
            subject=self.subject,
            word_count=self.word_count,
            summary=self.description,
        )
        intro = Chapter(
            id="intro",
            title="书籍简介",
            content=intro_html,
            filename="intro.xhtml",
            css=[self.intro_css],
        )
        self.chapters.append(intro)
        self._register(intro, folder=TEXT_FOLDER)
        self.nav.add_chapter(intro.id, intro.title, f"{TEXT_FOLDER}/{intro.filename}")
        self.ncx.add_chapter(intro.id, intro.title, f"{TEXT_FOLDER}/{intro.filename}")

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

            # container
            epub.writestr(
                "META-INF/container.xml",
                build_container_xml(),
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
            for css in self.styles:
                path = f"{ROOT_PATH}/{CSS_FOLDER}/{css.filename}"
                epub.writestr(path, css.content, compress_type=ZIP_DEFLATED)

            # chapters
            for chap in self.chapters:
                path = f"{ROOT_PATH}/{TEXT_FOLDER}/{chap.filename}"
                epub.writestr(path, chap.to_xhtml(), compress_type=ZIP_DEFLATED)

            # images
            for img in self.images:
                path = f"{ROOT_PATH}/{IMAGE_FOLDER}/{img.filename}"
                epub.writestr(path, img.data, compress_type=ZIP_DEFLATED)

        return output_path
