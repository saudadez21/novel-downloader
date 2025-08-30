#!/usr/bin/env python3
"""
novel_downloader.core.parsers.esjzone
-------------------------------------

"""

import re
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import (
    BookInfoDict,
    ChapterDict,
    VolumeInfoDict,
)


@register_parser(
    site_keys=["esjzone"],
)
class EsjzoneParser(BaseParser):
    """
    Parser for esjzone book pages.
    """

    # Chapter XPaths
    _CHAPTER_TEXT_XPATH = 'string(//div[contains(@class, "forum-content")])'
    _CHAPTER_CONTENT_NODES_XPATH = '//div[contains(@class, "forum-content")]/*'
    _CHAPTER_TIME_XPATHS = [
        '//i[contains(@class, "icon-clock")]/following-sibling::text()',
        '//i[contains(@class, "icon-pen-tool")]/following-sibling::text()',
    ]
    _CHECK_FORUM_XPATH = '//div[@class="page-title"]//ul[@class="breadcrumbs"]/li[not(@class="slash")]//text()'  # noqa: E501

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        注: 由于网站使用了多种不同的分卷格式, 已经尝试兼容常见情况,
        但仍可能存在未覆盖的 cases

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list or self._is_forum_page(html_list):
            return None

        tree = html.fromstring(html_list[0])

        # --- Basic metadata ---
        book_name = self._first_str(
            tree.xpath('//h2[contains(@class,"text-normal")]/text()')
        )
        author = self._first_str(tree.xpath('//li[strong[text()="作者:"]]/a/text()'))
        cover_url = self._first_str(
            tree.xpath('//div[contains(@class,"product-gallery")]//img/@src')
        )
        update_time = self._first_str(
            tree.xpath('//li[strong[text()="更新日期:"]]/text()')
        )  # noqa: E501
        word_count = self._first_str(
            tree.xpath('//span[@id="txt"]/text()'), replaces=[(",", "")]
        )
        book_type = self._first_str(tree.xpath('//li[strong[text()="類型:"]]/text()'))
        alt_name = self._first_str(
            tree.xpath('//li[strong[text()="其他書名:"]]/text()')
        )  # noqa: E501
        web_url = self._first_str(tree.xpath('//li[strong[text()="Web生肉:"]]/a/@href'))

        # Summary paragraphs
        paras = tree.xpath('//div[@class="description"]/p')
        texts = [p.xpath("string()").strip() for p in paras]
        summary = "\n".join(t for t in texts if t)

        current_vol: VolumeInfoDict = {
            "volume_name": "單卷",
            "chapters": [],
        }
        volumes: list[VolumeInfoDict] = [current_vol]

        def _is_garbage_title(name: str) -> bool:
            stripped = name.strip()
            return not stripped or bool(re.fullmatch(r"[\W_]+", stripped))

        def _start_volume(name: str) -> None:
            nonlocal current_vol
            if _is_garbage_title(name):
                return
            name = name.strip() or "未命名卷"
            if current_vol and current_vol["volume_name"] == name:
                return
            current_vol = {"volume_name": name, "chapters": []}
            volumes.append(current_vol)

        nodes = tree.xpath('//div[@id="chapterList"]/*')
        for node in nodes:
            tag = node.tag.lower()

            if tag == "details":
                # ---- DETAILS-based layout ----
                vol_name = node.xpath("string(./summary)").strip() or "未命名卷"
                _start_volume(vol_name)

                # all chapters inside this details
                for a in node.findall("a"):
                    title = "".join(a.xpath(".//p//text()")).strip()
                    href = a.get("href", "")
                    chap_id = href.rstrip("/").split("/")[-1].split(".", 1)[0]
                    current_vol["chapters"].append(
                        {
                            "title": title,
                            "url": href,
                            "chapterId": chap_id,
                        }
                    )

            elif (
                tag in ("h2",)
                or (tag == "p" and node.get("class") == "non")
                or tag == "summary"
            ):
                # Handle possible volume title markers:
                # - <h2>: standard volume header
                # - <p class="non">: alternative volume header style
                # - <summary>: fallback for stray <summary> tags outside <details>
                _start_volume(node.xpath("string()"))

            elif tag == "a":
                # ---- chapter link, attach to current volume ----
                title = "".join(node.xpath(".//p//text()")).strip()
                href = node.get("href", "")
                chap_id = href.rstrip("/").split("/")[-1].split(".", 1)[0]
                current_vol["chapters"].append(
                    {"title": title, "url": href, "chapterId": chap_id}
                )
        volumes = [vol for vol in volumes if vol["chapters"]]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "summary": summary,
            "tags": [book_type],
            "word_count": word_count,
            "volumes": volumes,
            "extra": {
                "alt_name": alt_name,
                "web_url": web_url,
            },
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list or self._is_forum_page(html_list):
            return None
        tree = html.fromstring(html_list[0])

        content_lines: list[str] = []
        content_nodes = tree.xpath(self._CHAPTER_CONTENT_NODES_XPATH)
        for node in content_nodes:
            if node.tag == "p":
                img_srcs = node.xpath(".//img/@src")
                if img_srcs:
                    for src in img_srcs:
                        content_lines.append(f'<img src="{src}" />')
                else:
                    text = "".join(node.xpath(".//text()")).strip()
                    if text:
                        content_lines.append(text)
            elif node.tag == "a":
                img_srcs = node.xpath(".//img/@src")
                for src in img_srcs:
                    content_lines.append(f'<img src="{src}" />')

        content = (
            "\n".join(content_lines).strip()
            if content_lines
            else tree.xpath(self._CHAPTER_TEXT_XPATH).strip()
        )
        if not content:
            return None

        title_nodes = tree.xpath("//h2/text()")
        title = title_nodes[0].strip() if title_nodes else ""

        updated_at = next(
            (
                x.strip()
                for xp in self._CHAPTER_TIME_XPATHS
                for x in tree.xpath(xp)
                if x.strip()
            ),
            "",
        )

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "esjzone", "updated_at": updated_at},
        }

    def _is_forum_page(self, html_str: list[str]) -> bool:
        if not html_str:
            return False

        tree = html.fromstring(html_str[0])
        page_title = tree.xpath('string(//div[@class="page-title"]//h1)').strip()
        if page_title != "論壇":
            return False
        breadcrumb: list[str] = tree.xpath(self._CHECK_FORUM_XPATH)
        breadcrumb = [s.strip() for s in breadcrumb if s.strip()]
        return breadcrumb == ["Home", "論壇"]
