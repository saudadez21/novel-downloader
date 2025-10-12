#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.exporter
------------------------------------------------
"""

from html import escape
from pathlib import Path
from typing import Any

from novel_downloader.libs.epub import Chapter, EpubBuilder, StyleSheet
from novel_downloader.plugins.common.exporter import CommonExporter
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict


@registrar.register_exporter()
class CiyuanjiExporter(CommonExporter):
    """
    Exporter for Ciyuanji (次元姬) novels.
    """

    _IMAGE_WRAPPER = '<div class="duokan-image-single illus">{img}</div>'

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
        Build a formatted chapter epub HTML including title, body paragraphs,
        and optional extra sections.
        """
        title = chap_title or chap.get("title", "").strip()
        content = chap.get("content", "")

        extras = chap.get("extra") or {}
        imgs_by_line = self._collect_img_map(extras)

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
        for url in imgs_by_line.get(0, []):
            _append_image(url)

        # Paragraphs + inline-after images
        for i, ln in enumerate(content.splitlines(), start=1):
            if s := ln.strip():
                html_parts.append(f"<p>{escape(s)}</p>")
            for url in imgs_by_line.get(i, []):
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
        Convert extras["imgList"] into {int -> [url, ...]}.
        """
        out: dict[int, list[str]] = {}
        img_list = extras.get("imgList")
        if not isinstance(img_list, list):
            return out
        for item in img_list:
            if not isinstance(item, dict):
                continue
            idx = item.get("paragraphIndex")
            url = item.get("imgUrl")
            if isinstance(idx, int) and isinstance(url, str):
                u = url.strip()
                if u:
                    out.setdefault(idx, []).append(u)
        return out
