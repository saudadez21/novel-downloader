#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.syosetu_org.parser
-------------------------------------------------
"""

from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class SyosetuOrgParser(BaseParser):
    """
    Parser for ハーメルン book pages.
    """

    site_name: str = "syosetu_org"
    BASE_URL = "https://syosetu.org"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Metadata
        book_name = self._first_str(
            tree.xpath('//div[@class="ss"]//span[@itemprop="name"]/text()')
        )
        author = self._first_str(
            tree.xpath('//div[@class="ss"]//span[@itemprop="author"]//a/text()')
        )
        tags: list[str] = []
        tag_nodes = tree.xpath(
            '(//div[@class="ss"])[1]//a[contains(@class,"alert_color")]/text()'
        )
        tag_nodes += tree.xpath(
            '(//div[@class="ss"])[1]//span[@itemprop="keywords"]//a/text()'
        )
        for t in tag_nodes:
            tag = t.strip()
            if tag and tag not in tags:
                tags.append(tag)

        summary_parts = [
            t.strip()
            for t in tree.xpath('(//div[@class="ss"])[2]//text()')
            if t.strip()
        ]
        summary = "\n".join(summary_parts)

        # Chapters extraction
        volumes: list[VolumeInfoDict] = []
        vol_idx: int = 1
        vol_name: str | None = None
        vol_chaps: list[ChapterInfoDict] = []

        def flush_volume() -> None:
            nonlocal vol_idx, vol_name, vol_chaps
            if not vol_chaps:
                return

            volumes.append(
                {
                    "volume_name": vol_name or f"未命名卷 {vol_idx}",
                    "chapters": vol_chaps,
                }
            )

            vol_name = None
            vol_chaps = []
            vol_idx += 1

        for table in tree.xpath('//div[@class="ss"]/table'):
            for tr in table.xpath(".//tr"):
                strong = tr.xpath(".//strong/text()")
                if strong:
                    flush_volume()
                    vol_name = strong[0].strip()
                    continue

                link = tr.xpath('.//a[@href and contains(@href,".html")]')
                if link:
                    a = link[0]
                    href = (a.get("href") or "").strip()
                    title = (a.text or "").strip()
                    chap_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                    vol_chaps.append(
                        {
                            "title": title,
                            "url": href,
                            "chapterId": chap_id,
                        }
                    )
        flush_volume()

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": "",
            "update_time": "",
            "tags": tags,
            "summary": summary,
            "volumes": volumes,
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

        title = self._join_strs(
            tree.xpath(
                '//span[@style[contains(.,"font-size") and contains(.,"120%")]]/text()'
            )
        )

        # Extract paragraphs of content
        maegaki = self._join_strs(tree.xpath('//div[@id="maegaki"]//text()'))
        atogaki = self._join_strs(tree.xpath('//div[@id="atogaki"]//text()'))
        paragraphs = [maegaki] if maegaki else []
        paragraphs.extend(
            stripped
            for p in tree.xpath('//div[@id="honbun"]/p')
            if (stripped := p.text_content().strip())
        )
        if atogaki:
            paragraphs.append(atogaki)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
