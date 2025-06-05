#!/usr/bin/env python3
"""
novel_downloader.core.parsers.esjzone.main_parser
-------------------------------------------------

"""

import re
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import ChapterDict


class EsjzoneParser(BaseParser):
    """ """

    # Book info XPaths
    _BOOK_NAME_XPATH = '//h2[contains(@class, "text-normal")]/text()'
    _AUTHOR_XPATH = '//li[strong[text()="作者:"]]/a/text()'
    _COVER_URL_XPATH = '//div[contains(@class,"product-gallery")]//img/@src'
    _UPDATE_TIME_XPATH = '//li[strong[text()="更新日期:"]]/text()'
    _WORD_COUNT_XPATH = '//span[@id="txt"]/text()'
    _TYPE_XPATH = '//li[strong[text()="類型:"]]/text()'
    _ALT_NAME_XPATH = '//li[strong[text()="其他書名:"]]/text()'
    _WEB_URL_XPATH = '//li[strong[text()="Web生肉:"]]/a/@href'
    _SUMMARY_XPATH = '//div[@class="description"]/p//text()'

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
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        注: 由于网站使用了多种不同的分卷格式, 已经尝试兼容常见情况,
        但仍可能存在未覆盖的 cases

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list or self._is_forum_page(html_list):
            return {}
        tree = html.fromstring(html_list[0])
        result: dict[str, Any] = {}

        result["book_name"] = self._get_text(tree, self._BOOK_NAME_XPATH)
        result["author"] = self._get_text(tree, self._AUTHOR_XPATH)
        result["cover_url"] = self._get_text(tree, self._COVER_URL_XPATH)
        result["update_time"] = self._get_text(tree, self._UPDATE_TIME_XPATH)
        result["word_count"] = self._get_text(
            tree, self._WORD_COUNT_XPATH, clean_comma=True
        )
        result["type"] = self._get_text(tree, self._TYPE_XPATH)
        result["alt_name"] = self._get_text(tree, self._ALT_NAME_XPATH)
        result["web_url"] = self._get_text(tree, self._WEB_URL_XPATH)
        # result["summary"] = self._get_text(tree, self._SUMMARY_XPATH, join=True)
        paras = tree.xpath('//div[@class="description"]/p')
        texts = [p.xpath("string()").strip() for p in paras]
        result["summary"] = "\n".join(texts).strip()

        volumes: list[dict[str, Any]] = []
        current_vol: dict[str, Any] = {}

        def _is_garbage_title(name: str) -> bool:
            stripped = name.strip()
            return not stripped or bool(re.fullmatch(r"[\W_]+", stripped))

        def _start_volume(name: str) -> None:
            nonlocal current_vol
            if _is_garbage_title(name):
                return
            name = name.strip() or "未命名卷"
            if name == "未命名卷" and current_vol is not None:
                return
            current_vol = {"volume_name": name, "chapters": []}
            volumes.append(current_vol)

        _start_volume("單卷")

        # nodes = tree.xpath('//div[@id="chapterList"]/details') + tree.xpath(
        #     '//div[@id="chapterList"]/*[not(self::details)]'
        # )
        nodes = tree.xpath('//div[@id="chapterList"]/*')

        for node in nodes:
            tag = node.tag.lower()

            if tag == "details":
                # ---- DETAILS-based layout ----
                summary = node.find("summary")
                vol_name = summary.text if summary is not None else "未命名卷"
                _start_volume(vol_name)

                # all chapters inside this details
                for a in node.findall("a"):
                    title = "".join(a.xpath(".//p//text()")).strip()
                    href = a.get("href", "")
                    chap_id = href.rstrip("/").split("/")[-1].split(".", 1)[0]
                    current_vol["chapters"].append(
                        {"title": title, "url": href, "chapterId": chap_id}
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
        result["volumes"] = volumes

        return result

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list or self._is_forum_page(html_list):
            return None
        tree = html.fromstring(html_list[0], parser=None)

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
            "\n\n".join(content_lines).strip()
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

    @staticmethod
    def _get_text(
        tree: html.HtmlElement,
        xpath: str,
        join: bool = False,
        clean_comma: bool = False,
    ) -> str:
        data = tree.xpath(xpath)
        if not data:
            return ""
        text = "\n".join(data) if join else data[0].strip()
        return text.replace(",", "") if clean_comma else text
