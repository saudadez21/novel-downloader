#!/usr/bin/env python3
"""
novel_downloader.plugins.common.exporter
----------------------------------------

Shared exporter implementation for producing standard TXT and EPUB outputs.
"""

from html import escape
from pathlib import Path
from typing import Any, Literal

from novel_downloader.infra.http_defaults import IMAGE_HEADERS
from novel_downloader.infra.paths import CSS_MAIN_PATH
from novel_downloader.libs.epub import (
    Chapter,
    EpubBuilder,
    StyleSheet,
    Volume,
)
from novel_downloader.libs.filesystem import img_name, sanitize_filename, write_file
from novel_downloader.plugins.base.exporter import BaseExporter
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


class CommonExporter(BaseExporter):
    """
    CommonExporter is a exporter that processes and exports novels.

    It extends the BaseExporter interface and provides
    logic for exporting full novels as plain text (.txt) files
    and EPUB (.epub) files.
    """

    _IMAGE_WRAPPER = '<div class="duokan-image-single illus">{img}</div>'

    def export_as_txt(self, book: BookConfig) -> Path | None:
        """
        Export a novel as a single text file by merging all chapter data.

        Steps:
          1. Load book metadata.
          2. For each volume:
            a. Append the volume title.
            b. Batch-fetch all chapters in that volume to minimize SQLite calls.
            c. Append each chapter's title, content, and optional extra data.
          3. Build a header with book metadata.
          4. Concatenate header and all chapter contents.
          5. Save the resulting .txt file to the output directory
        """
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        # --- Load book data ---
        book_info = self._load_stage_data(book_id)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return None

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""
        header_txt = self._build_txt_header(book_info, name, author)

        # --- Build body by volumes & chapters ---
        parts: list[str] = [header_txt]

        for v_idx, volume in enumerate(vols, start=1):
            vol_title = volume.get("volume_name") or f"卷 {v_idx}"
            parts.append(self._build_txt_volume_heading(vol_title, volume))

            # Collect chapter ids then batch fetch
            cids = [
                c["chapterId"] for c in volume.get("chapters", []) if c.get("chapterId")
            ]
            if not cids:
                continue

            chap_map = self._get_chapters(book_id, cids)
            for ch_info in volume.get("chapters", []):
                cid = ch_info.get("chapterId")
                ch_title = ch_info.get("title")
                if not cid:
                    continue

                ch = chap_map.get(cid)
                if not ch:
                    self._handle_missing_chapter(book_id, cid)
                    continue

                parts.append(self._build_txt_chapter(ch_title, ch))

        final_text = "\n".join(parts)

        # --- Determine output file path ---
        out_name = self.get_filename(title=name, author=author, ext="txt")
        out_path = self._output_dir / sanitize_filename(out_name)

        # --- Save final text ---
        try:
            result = write_file(
                content=final_text, filepath=out_path, on_exist="overwrite"
            )
            self.logger.info(
                "Exported TXT (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            self.logger.error(
                "Failed to write TXT (site=%s, book=%s) to %s: %s",
                self._site,
                book_id,
                out_path,
                e,
                exc_info=True,
            )
            return None
        return result

    def export_as_epub(self, book: BookConfig) -> Path | None:
        mode = self._split_mode
        if mode == "book":
            return self._export_epub_by_book(book)
        if mode == "volume":
            return self._export_epub_by_volume(book)
        raise ValueError(f"Unsupported split_mode: {mode!r}")

    def _export_epub_by_volume(self, book: BookConfig) -> Path | None:
        """
        Export each volume of a novel as a separate EPUB file.

        Steps:
          1. Load `book_info` for metadata.
          2. For each volume:
             a. Clean the volume title and determine output filename.
             b. Batch-fetch all chapters in this volume to minimize SQLite overhead.
             c. Initialize an EPUB builder for the volume, including cover and intro.
             d. For each chap: build XHTML and place image from extras.image_positions
             e. Finalize and write the volume EPUB.
        """
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        # --- Load book data ---
        book_info = self._load_stage_data(book_id)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return None

        # --- Prepare path ---
        raw_base = self._raw_data_dir / book_id
        img_dir = raw_base / "images"
        img_dir.mkdir(parents=True, exist_ok=True)

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""
        book_summary = book_info.get("summary", "")

        # --- Generate intro + cover ---
        cover_url = book_info.get("cover_url") or ""
        cover_path: Path | None = None
        if self._include_cover and cover_url:
            cover_path = self._download_image(
                img_url=cover_url,
                target_dir=raw_base,
                filename="cover",
            )

        css_text = CSS_MAIN_PATH.read_text(encoding="utf-8")
        main_css = StyleSheet(id="main_style", content=css_text, filename="main.css")

        # --- Compile columes ---
        for v_idx, vol in enumerate(vols, start=1):
            vol_title = vol.get("volume_name") or f"卷 {v_idx}"

            vol_cover_url = vol.get("volume_cover") or ""
            vol_cover: Path | None = None
            if self._include_cover and vol_cover_url:
                vol_cover = self._download_image(
                    img_url=vol_cover_url,
                    target_dir=img_dir,
                )
            vol_cover = vol_cover or cover_path

            epub = EpubBuilder(
                title=f"{name} - {vol_title}",
                author=author,
                description=vol.get("volume_intro") or book_summary,
                cover_path=vol_cover,
                subject=book_info.get("tags", []),
                serial_status=book_info.get("serial_status", ""),
                word_count=vol.get("word_count", ""),
                uid=f"{self._site}_{book_id}_v{v_idx}",
            )
            epub.add_stylesheet(main_css)

            # Collect chapter ids then batch fetch
            cids = [
                c["chapterId"] for c in vol.get("chapters", []) if c.get("chapterId")
            ]
            if not cids:
                continue
            chap_map = self._get_chapters(book_id, cids)

            # Append each chapter
            seen_cids: set[str] = set()
            for ch_info in vol.get("chapters", []):
                cid = ch_info.get("chapterId")
                ch_title = ch_info.get("title")
                if not cid or cid in seen_cids:
                    continue

                ch = chap_map.get(cid)
                if not ch:
                    self._handle_missing_chapter(book_id, cid)
                    continue

                chapter_obj = self._build_epub_chapter(
                    book=epub,
                    css=[main_css],
                    cid=cid,
                    chap_title=ch_title,
                    chap=ch,
                    img_dir=img_dir,
                )
                epub.add_chapter(chapter_obj)
                seen_cids.add(cid)

            out_name = self.get_filename(title=vol_title, author=author, ext="epub")
            out_path = self._output_dir / sanitize_filename(out_name)

            try:
                epub.export(out_path)
                self.logger.info(
                    "Exported EPUB (site=%s, book=%s): %s",
                    self._site,
                    book_id,
                    out_path,
                )
            except Exception as e:
                self.logger.error(
                    "Failed to write EPUB (site=%s, book=%s) to %s: %s",
                    self._site,
                    book_id,
                    out_path,
                    e,
                    exc_info=True,
                )

        return None

    def _export_epub_by_book(self, book: BookConfig) -> Path | None:
        """
        Export a single novel (identified by `book_id`) to an EPUB file.

        This function will:
          1. Load `book_info` for metadata.
          2. Generate introductory HTML and optionally include the cover image.
          3. Initialize the EPUB container.
          4. Iterate through volumes and chapters in volume-batches, convert to XHTML.
          5. Assemble the spine, TOC, CSS and write out the final `.epub`.

        :param book_id: Identifier of the novel (used as subdirectory name).
        """
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        # --- Load book data ---
        book_info = self._load_stage_data(book_id)

        # --- Filter volumes & chapters ---
        orig_vols = book_info.get("volumes", [])
        vols = self._filter_volumes(orig_vols, start_id, end_id, ignore_set)
        if not vols:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return None

        # --- Prepare path ---
        raw_base = self._raw_data_dir / book_id
        img_dir = raw_base / "images"
        img_dir.mkdir(parents=True, exist_ok=True)

        # --- Prepare header (book metadata) ---
        name = book_info["book_name"]
        author = book_info.get("author") or ""

        # --- Generate intro + cover ---
        cover_url = book_info.get("cover_url") or ""
        cover_path: Path | None = None
        if self._include_cover and cover_url:
            cover_path = self._download_image(
                img_url=cover_url,
                target_dir=raw_base,
                filename="cover",
            )

        # --- Initialize EPUB ---
        epub = EpubBuilder(
            title=name,
            author=author,
            description=book_info.get("summary", ""),
            cover_path=cover_path,
            subject=book_info.get("tags", []),
            serial_status=book_info.get("serial_status", ""),
            word_count=book_info.get("word_count", ""),
            uid=f"{self._site}_{book_id}",
        )
        css_text = CSS_MAIN_PATH.read_text(encoding="utf-8")
        main_css = StyleSheet(id="main_style", content=css_text, filename="main.css")
        epub.add_stylesheet(main_css)

        # --- Compile columes ---
        seen_cids: set[str] = set()
        for v_idx, vol in enumerate(vols, start=1):
            vol_title = vol.get("volume_name") or f"卷 {v_idx}"

            vol_cover_url = vol.get("volume_cover") or ""
            vol_cover: Path | None = None
            if self._include_cover and vol_cover_url:
                vol_cover = self._download_image(
                    img_url=vol_cover_url,
                    target_dir=img_dir,
                )

            curr_vol = Volume(
                id=f"vol_{v_idx}",
                title=vol_title,
                intro=vol.get("volume_intro", ""),
                cover=vol_cover,
            )

            # Collect chapter ids then batch fetch
            cids = [
                c["chapterId"] for c in vol.get("chapters", []) if c.get("chapterId")
            ]
            if not cids:
                epub.add_volume(curr_vol)
                continue
            chap_map = self._get_chapters(book_id, cids)

            # Append each chapter
            for ch_info in vol.get("chapters", []):
                cid = ch_info.get("chapterId")
                ch_title = ch_info.get("title")
                if not cid or cid in seen_cids:
                    continue

                ch = chap_map.get(cid)
                if not ch:
                    self._handle_missing_chapter(book_id, cid)
                    continue

                chapter_obj = self._build_epub_chapter(
                    book=epub,
                    css=[main_css],
                    cid=cid,
                    chap_title=ch_title,
                    chap=ch,
                    img_dir=img_dir,
                )

                curr_vol.chapters.append(chapter_obj)
                seen_cids.add(cid)

            if curr_vol.chapters:
                epub.add_volume(curr_vol)

        # --- Finalize EPUB ---
        out_name = self.get_filename(title=name, author=author, ext="epub")
        out_path = self._output_dir / sanitize_filename(out_name)

        try:
            epub.export(out_path)
            self.logger.info(
                "Exported EPUB (site=%s, book=%s): %s", self._site, book_id, out_path
            )
        except Exception as e:
            self.logger.error(
                "Failed to write EPUB (site=%s, book=%s) to %s: %s",
                self._site,
                book_id,
                out_path,
                e,
                exc_info=True,
            )
            return None
        return out_path

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        """
        Normalize a book identifier.

        Subclasses may override this method to transform the book ID
        into their preferred format.
        """
        return book_id.replace("/", "-")

    def _render_txt_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    def _render_epub_extras(self, extras: dict[str, Any]) -> str:
        """
        Format the extras dict into a string.

        Subclasses may override this method to render extra info.
        """
        return ""

    @staticmethod
    def _download_image(
        img_url: str,
        target_dir: Path,
        filename: str | None = None,
        *,
        on_exist: Literal["overwrite", "skip"] = "overwrite",
    ) -> Path | None:
        """
        Download image from url to target dir with given name

        Subclasses may override this method if site need more info
        """
        from novel_downloader.infra.network import download

        return download(
            img_url,
            target_dir,
            filename=img_name(img_url, name=filename),
            headers=IMAGE_HEADERS,
            on_exist=on_exist,
            retries=0,
        )

    @staticmethod
    def _filter_volumes(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: set[str],
    ) -> list[VolumeInfoDict]:
        """
        Rebuild volumes to include only chapters within
        the [start_id, end_id] range (inclusive),
        while excluding any chapter IDs in `ignore`.

        :param vols: List of volume dicts.
        :param start_id: Range start chapter ID (inclusive) or None to start.
        :param end_id: Range end chapter ID (inclusive) or None to go till the end.
        :param ignore: Set of chapter IDs to exclude (regardless of range).
        :return: New list of volumes with chapters filtered accordingly.
        """
        if start_id is None and end_id is None and not ignore:
            return vols

        started = start_id is None
        finished = False
        result: list[VolumeInfoDict] = []

        for vol in vols:
            if finished:
                break

            kept: list[ChapterInfoDict] = []

            for ch in vol.get("chapters", []):
                cid = ch.get("chapterId")
                if not cid:
                    continue

                # wait until hit the start_id
                if not started:
                    if cid == start_id:
                        started = True
                    else:
                        continue

                if cid not in ignore:
                    kept.append(ch)

                # check for end_id after keeping
                if end_id is not None and cid == end_id:
                    finished = True
                    break

            if kept:
                result.append(
                    {
                        **vol,
                        "chapters": kept,
                    }
                )

        return result

    def _build_txt_header(self, book_info: BookInfoDict, name: str, author: str) -> str:
        """
        Top-of-file metadata block.
        """
        lines: list[str] = [name.strip()]

        if author:
            lines.append(f"作者：{author.strip()}")

        if serial_status := book_info.get("serial_status"):
            lines.append(f"状态：{serial_status.strip()}")

        if word_count := book_info.get("word_count"):
            lines.append(f"字数：{word_count.strip()}")

        if tags_list := book_info.get("tags"):
            tags = "、".join(t.strip() for t in tags_list if t)
            if tags:
                lines.append(f"标签：{tags}")

        if update_time := (book_info.get("update_time") or "").strip():
            lines.append(f"更新：{update_time}")

        if summary := (book_info.get("summary") or "").strip():
            lines.extend(["", summary])

        return "\n".join(lines).strip() + "\n\n"

    def _build_txt_volume_heading(self, vol_title: str, volume: VolumeInfoDict) -> str:
        """
        Render a volume heading. Include optional info if present.
        """
        meta_bits: list[str] = []

        if v_update_time := volume.get("update_time"):
            meta_bits.append(f"更新时间：{v_update_time}")

        if v_word_count := volume.get("word_count"):
            meta_bits.append(f"字数：{v_word_count}")

        if v_intro := (volume.get("volume_intro") or "").strip():
            meta_bits.append(f"简介：{v_intro}")

        line = f"=== {vol_title.strip()} ==="
        return f"{line}\n" + ("\n".join(meta_bits) + "\n\n" if meta_bits else "\n\n")

    def _build_txt_chapter(self, chap_title: str | None, chap: ChapterDict) -> str:
        """
        Render one chapter to text
        """
        # Title
        title_line = chap_title or chap.get("title", "").strip()

        cleaned = chap.get("content", "").strip()
        body = "\n".join(s for line in cleaned.splitlines() if (s := line.strip()))

        # Extras
        extras_txt = self._render_txt_extras(chap.get("extra", {}) or {})

        return (
            f"{title_line}\n\n{body}\n\n{extras_txt}\n\n"
            if extras_txt
            else f"{title_line}\n\n{body}\n\n"
        )

    def _build_epub_chapter(
        self,
        *,
        book: EpubBuilder,
        css: list[StyleSheet],
        cid: str,
        chap_title: str | None,
        chap: ChapterDict,
        img_dir: Path,
    ) -> Chapter:
        """
        Build a Chapter object with XHTML content and optionally place images
        from `chap.extra['image_positions']` (1-based index; 0 = before 1st paragraph).
        """
        title = chap_title or chap.get("title", "").strip()
        content = chap.get("content", "")

        extras = chap.get("extra") or {}
        image_positions = self._collect_img_map(extras)
        html_parts: list[str] = [f"<h2>{escape(title)}</h2>"]

        def _append_image(url: str) -> None:
            if not self._include_picture:
                return
            u = (url or "").strip()
            if not u:
                return
            if u.startswith("//"):
                u = "https:" + u
            if not (u.startswith("http://") or u.startswith("https://")):
                return
            try:
                local = self._download_image(u, img_dir, on_exist="skip")
                if not local:
                    return
                fname = book.add_image(local)
                img = f'<img src="../Images/{fname}" alt="image"/>'
                html_parts.append(self._IMAGE_WRAPPER.format(img=img))
            except Exception as e:
                self.logger.debug("EPUB image add failed for %s: %s", u, e)

        # Images before first paragraph
        for url in image_positions.get(0, []):
            _append_image(url)

        # Paragraphs + inline-after images
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            if ln := line.strip():
                html_parts.append(f"<p>{escape(ln)}</p>")
            for url in image_positions.get(i, []):
                _append_image(url)

        max_i = len(lines)
        for k, urls in image_positions.items():
            if k > max_i:
                for url in urls:
                    _append_image(url)

        if extras_epub := self._render_epub_extras(extras):
            html_parts.append(extras_epub)

        xhtml = "\n".join(html_parts)
        return Chapter(
            id=f"c_{cid}",
            filename=f"c{cid}.xhtml",
            title=title,
            content=xhtml,
            css=css,
        )

    @staticmethod
    def _collect_img_map(extras: dict[str, Any]) -> dict[int, list[str]]:
        """
        Collect and normalize `image_positions` into `{int: [str, ...]}`.
        """
        result: dict[int, list[str]] = {}
        raw_map = extras.get("image_positions")

        if not isinstance(raw_map, dict):
            return result
        for k, v in raw_map.items():
            try:
                key = int(k)
            except Exception:
                key = 0
            urls: list[str] = []
            if isinstance(v, list | tuple):
                for u in v:
                    if isinstance(u, str):
                        s = u.strip()
                        if s:
                            urls.append(s)
            elif isinstance(v, str):
                s = v.strip()
                if s:
                    urls.append(s)
            if urls:
                result.setdefault(key, []).extend(urls)
        return result

    @classmethod
    def _render_html_block(cls, text: str) -> str:
        """
        Wraps each non-empty (stripped) line with <p>.
        """
        return "\n".join(
            f"<p>{escape(s)}</p>" for ln in text.splitlines() if (s := ln.strip())
        )
