#!/usr/bin/env python3
"""
novel_downloader.core.parsers.yamibo.main_parser
------------------------------------------------

"""

from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import ChapterDict


class YamiboParser(BaseParser):
    """ """

    BASE_URL = "https://www.yamibo.com"
    # Book info XPaths
    _BOOK_NAME_XPATH = 'string(//h3[contains(@class, "col-md-12")])'
    _AUTHOR_XPATH = 'string(//h5[contains(@class, "text-warning")])'
    _COVER_URL_XPATH = '//img[contains(@class, "img-responsive")]/@src'
    _UPDATE_TIME_XPATH = '//p[contains(text(), "更新时间：")]'
    _SERIAL_STATUS_XPATH = '//p[contains(text(), "作品状态：")]'
    _TYPE_XPATH = '//p[contains(text(), "作品分类：")]'
    _SUMMARY_XPATH = 'string(//div[@id="w0-collapse1"]/div)'

    _VOLUME_NODE_XPATH = (
        '//div[contains(@class, "panel-info") and contains(@class, "panel-default")]'
    )
    _VOLUME_TITLE_XPATH = './/div[contains(@class, "panel-heading")]//a/text()'
    _CHAPTER_NODE_XPATH = (
        './/div[contains(@class, "panel-body")]//a[contains(@href, "view-chapter")]'
    )
    _CHAPTER_FLAT_XPATH = (
        '//div[@class="panel-body"]//a[contains(@href, "view-chapter")]'
    )

    # Chapter field XPaths
    _CHAPTER_TITLE_XPATH = "string(//section[contains(@class, 'col-md-9')]//h3)"
    _CHAPTER_TIME_XPATH = (
        "//div[contains(@class, 'row')]//div[contains(text(), '更新时间')]"
    )
    _CHAPTER_WORD_COUNT_XPATH = (
        "//div[contains(@class, 'row')]//div[contains(text(), '章节字数')]"
    )
    _CHAPTER_CONTENT_XPATH = "//div[@id='w0-collapse1']//p//text()"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return {}

        tree = html.fromstring(html_list[0])
        result: dict[str, Any] = {}

        result["book_name"] = tree.xpath(self._BOOK_NAME_XPATH).strip()
        result["author"] = tree.xpath(self._AUTHOR_XPATH).strip()

        cover = tree.xpath(self._COVER_URL_XPATH)
        result["cover_url"] = f"{self.BASE_URL}{cover[0]}" if cover else ""

        update_node = tree.xpath(self._UPDATE_TIME_XPATH)
        result["update_time"] = (
            update_node[0].xpath("string()").replace("更新时间：", "").strip()
            if update_node
            else ""
        )

        serial_node = tree.xpath(self._SERIAL_STATUS_XPATH)
        result["serial_status"] = (
            serial_node[0].xpath("string()").replace("作品状态：", "").strip()
            if serial_node
            else ""
        )

        type_node = tree.xpath(self._TYPE_XPATH)
        result["type"] = (
            type_node[0].xpath("string()").replace("作品分类：", "").strip()
            if type_node
            else ""
        )

        result["summary"] = tree.xpath(self._SUMMARY_XPATH).strip()

        volumes = []
        volume_nodes = tree.xpath(self._VOLUME_NODE_XPATH)

        if volume_nodes:
            for volume_node in volume_nodes:
                title_node = volume_node.xpath(self._VOLUME_TITLE_XPATH)
                volume_name = title_node[0].strip() if title_node else "未命名卷"

                chapter_nodes = volume_node.xpath(self._CHAPTER_NODE_XPATH)
                chapters = []
                for chap in chapter_nodes:
                    title = chap.xpath("string()").strip()
                    url = chap.get("href", "")
                    chapter_id = url.split("id=")[-1] if "id=" in url else ""
                    chapters.append(
                        {
                            "title": title,
                            "url": url,
                            "chapterId": chapter_id,
                        }
                    )

                volumes.append(
                    {
                        "volume_name": volume_name,
                        "chapters": chapters,
                    }
                )

        else:
            # fallback: flat list
            chapter_nodes = tree.xpath(self._CHAPTER_FLAT_XPATH)
            chapters = []
            for chap in chapter_nodes:
                title = chap.xpath("string()").strip()
                url = chap.get("href", "")
                chapter_id = url.split("id=")[-1] if "id=" in url else ""
                chapters.append(
                    {
                        "title": title,
                        "url": url,
                        "chapterId": chapter_id,
                    }
                )

            volumes = [
                {
                    "volume_name": "单卷",
                    "chapters": chapters,
                }
            ]

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
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        content_lines = tree.xpath(self._CHAPTER_CONTENT_XPATH)
        content = "\n\n".join(line.strip() for line in content_lines if line.strip())
        if not content:
            return None

        title = tree.xpath(self._CHAPTER_TITLE_XPATH).strip()

        update_node = tree.xpath(self._CHAPTER_TIME_XPATH)
        updated_at = (
            update_node[0].text.strip().replace("更新时间：", "") if update_node else ""
        )

        word_node = tree.xpath(self._CHAPTER_WORD_COUNT_XPATH)
        word = word_node[0].text.strip().replace("章节字数：", "") if word_node else ""
        word_count = int(word) if word.isdigit() else 0

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": "yamibo",
                "word_count": word_count,
                "updated_at": updated_at,
            },
        }
