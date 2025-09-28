#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shencou.parser
---------------------------------------------

"""

from typing import Any

from lxml import etree, html

from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class ShencouParser(BaseParser):
    """
    Parser for 神凑轻小说 book pages.
    """

    site_name: str = "shencou"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # --- Metadata ---
        raw_name = self._first_str(info_tree.xpath("//span//a/text()"))
        book_name = raw_name[:-2] if raw_name.endswith("小说") else raw_name

        author = self._first_str(
            info_tree.xpath('//td[contains(text(),"小说作者")]/text()'),
            replaces=[("小说作者：", "")],
        )

        cover_url = self._first_str(
            info_tree.xpath('//a[contains(@href,"/files/article/image")]/img/@src')
        )

        # word count
        word_count = self._first_str(
            info_tree.xpath('//td[contains(text(),"全文长度")]/text()'),
            replaces=[("全文长度：", "")],
        )

        # update time
        update_time = self._first_str(
            info_tree.xpath('//td[contains(text(),"最后更新")]/text()'),
            replaces=[("最后更新：", "")],
        )

        # serial status
        serial_status = self._first_str(
            info_tree.xpath('//td[contains(text(),"写作进度")]/text()'),
            replaces=[("写作进度：", "")],
        )

        # summary
        raw_detail = self._norm_space(
            info_tree.xpath('string(//td[@width="80%" and @valign="top"])')
        )
        summary = ""
        if "内容简介：" in raw_detail and "本书公告：" in raw_detail:
            intro = raw_detail.split("内容简介：", 1)[1]
            summary = intro.split("本书公告：", 1)[0].strip()

        # --- Catalog / Chapters ---
        volumes: list[VolumeInfoDict] = []
        curr_vol: VolumeInfoDict = {"volume_name": "未命名卷", "chapters": []}

        # Walk through volume headers (.zjbox) and lists (.zjlist4) in document order
        for elem in catalog_tree.xpath(
            '//div[@class="zjbox"] | //div[@class="zjlist4"]'
        ):
            cls_attr = elem.get("class", "")
            if "zjbox" in cls_attr:
                # before starting new volume, save the previous if it has chapters
                if curr_vol["chapters"]:
                    volumes.append(curr_vol)
                # start a new volume
                vol_name = elem.xpath(".//h2/text()")[0].strip()
                curr_vol = {"volume_name": vol_name, "chapters": []}
            elif "zjlist4" in cls_attr:
                # collect all <li><a> entries under this list
                for a in elem.xpath(".//ol/li/a"):
                    url = a.get("href").strip()
                    title = a.text_content().strip()
                    # '203740.html' -> '203740'
                    chap_id = url.split(".")[0]
                    curr_vol["chapters"].append(
                        {
                            "title": title,
                            "url": url,
                            "chapterId": chap_id,
                        }
                    )

        # append last volume if not empty
        if curr_vol["chapters"]:
            volumes.append(curr_vol)

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "summary": summary,
            "volumes": volumes,
            "word_count": word_count,
            "serial_status": serial_status,
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])
        title = self._first_str(tree.xpath("//h1/text()"))
        if not title:
            return None

        # strip book-name prefix if present
        bc = tree.xpath('//div[@id="breadCrumb"]//a/text()')
        if len(bc) >= 2:
            book_name = bc[1].strip()
            title = title.removeprefix(book_name).lstrip(" ：:–—-").strip()

        anchors = tree.xpath('//div[@id="BookSee_Right"]')
        if not anchors:
            return None
        marker = anchors[0]

        lines: list[str] = []

        def _append_text(text: str) -> None:
            for ln in text.replace("\xa0", " ").splitlines():
                ln2 = ln.strip()
                if ln2:
                    lines.append(ln2)

        if marker.tail:
            _append_text(marker.tail)

        # 4. Walk through siblings until <!--over-->
        node = marker
        while True:
            sib = node.getnext()
            if sib is None:
                break
            node = sib

            # Stop on the closing comment
            if isinstance(sib, etree._Comment) and "over" in (sib.text or ""):
                break

            # Process comment tails (e.g. <!--go--> tail)
            if isinstance(sib, etree._Comment):
                if sib.tail:
                    _append_text(sib.tail)
                continue

            if isinstance(sib, html.HtmlElement):
                # tag = sib.tag.lower()
                tag = str(sib.tag).lower()
                cls = sib.get("class", "") or ""

                if tag == "div" and "divimage" in cls:
                    srcs = sib.xpath(".//img/@src")
                    if srcs:
                        lines.append(f'<img src="{srcs[0]}" />')
                    # text after the div
                    if sib.tail:
                        _append_text(sib.tail)
                    continue

                if tag == "br":
                    if sib.tail:
                        _append_text(sib.tail)
                    continue

                text = sib.text_content()
                _append_text(text)
                if sib.tail:
                    _append_text(sib.tail)
                continue

        content = "\n".join(lines)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
