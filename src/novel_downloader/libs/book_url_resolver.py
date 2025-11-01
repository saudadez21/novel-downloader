#!/usr/bin/env python3
"""
novel_downloader.libs.book_url_resolver
---------------------------------------

Utility for resolving a novel site URL into a standardized configuration.
"""

from __future__ import annotations

__all__ = ["resolve_book_url"]

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict
from urllib.parse import urlparse

from novel_downloader.schemas import BookConfig

logger = logging.getLogger(__name__)


class BookURLInfo(TypedDict):
    book: BookConfig
    site_key: str


@dataclass
class BookIdExtractor:
    pattern: str
    build_book_id: Callable[[re.Match[str]], str]
    pattern_query: str | None = None
    build_book_id_query: Callable[[re.Match[str]], str] | None = None


@dataclass
class HintRule:
    pattern: str
    hint: str


@dataclass
class SiteRuleSet:
    site_key: str
    extractors: list[BookIdExtractor]
    hints: list[HintRule]


# -----------------------
# Host alias mapping
# -----------------------
HOST_ALIASES: dict[str, str] = {
    # 8novel info/chap domains
    "www.8novel.com": "8novel.com",
    "article.8novel.com": "8novel.com",
    # blqudu info/chap domains
    "www.blqudu.cc": "blqudu.cc",
    "www.biqudv.cc": "blqudu.cc",
    # hetushu simplified/traditional domains
    "www.hetushu.com": "hetushu.com",
    "www.hetubook.com": "hetushu.com",
    # dxmwx simplified/traditional
    "www.dxmwx.org": "dxmwx.org",
    "tw.dxmwx.org": "dxmwx.org",
    # lnovel simplified/traditional
    # "lnovel.org": "lnovel.org",
    "lnovel.tw": "lnovel.org",
    # quanben5 simplified/traditional
    "quanben5.com": "quanben5.com",
    "big5.quanben5.com": "quanben5.com",
    # ttkan main + region
    "www.ttkan.co": "ttkan.co",
    "cn.ttkan.co": "ttkan.co",
    "tw.ttkan.co": "ttkan.co",
    "www.wa01.com": "ttkan.co",
    "cn.wa01.com": "ttkan.co",
    "tw.wa01.com": "ttkan.co",
    # yibige variants
    "www.yibige.org": "yibige.org",
    "sg.yibige.org": "yibige.org",
    "tw.yibige.org": "yibige.org",
    "hk.yibige.org": "yibige.org",
    # xszj simplified/traditional
    "m.xszj.org": "xszj.org",
    # wxsck
    "www.wxscs.com": "wxsck.com",
}


def _normalize_host_and_path(url: str) -> tuple[str, str, str]:
    """
    Normalize a given URL:
      * Apply HOST_ALIASES mapping to unify different netlocs.
      * Return (canonical_host, path).
    """
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    host = HOST_ALIASES.get(netloc, netloc)
    path = parsed.path or "/"
    query = parsed.query or ""
    return host, path, query


# -----------------------
# Site-specific rules
# -----------------------
SITE_RULES: dict[str, list[SiteRuleSet]] = {
    "www.aaatxt.com": [
        SiteRuleSet(
            site_key="aaatxt",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/shu/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/yuedu/(\d+)_\d+\.html",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.akatsuki-novels.com": [
        SiteRuleSet(
            site_key="akatsuki_novels",
            extractors=[
                BookIdExtractor(
                    pattern=r"novel_id~(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.alicesw.com": [
        SiteRuleSet(
            site_key="alicesw",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/other/chapters/id/(\d+)\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/book/\d+/[A-Za-z0-9]+\.html$",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                ),
            ],
        )
    ],
    "www.alphapolis.co.jp": [
        SiteRuleSet(
            site_key="alphapolis",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)/(\d+)",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.b520.cc": [
        SiteRuleSet(
            site_key="b520",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+_\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.biquge5.com": [
        SiteRuleSet(
            site_key="biquge5",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+_\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.biquge345.com": [
        SiteRuleSet(
            site_key="biquge345",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(?:book|chapter)/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.biquguo.com": [
        SiteRuleSet(
            site_key="biquguo",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    # "biquyuedu.com": [SiteRuleSet(
    #     site_key="biquyuedu",
    #     extractors=[
    #         BookIdExtractor(
    #             pattern=r"^/novel/([^/]+)/\d+\.html$",
    #             build_book_id=lambda m: m.group(1),
    #         ),
    #         BookIdExtractor(
    #             pattern=r"^/novel/([^.]+)\.html",
    #             build_book_id=lambda m: m.group(1),
    #         ),
    #     ],
    #     hints=[],
    # )],
    "m.bixiange.me": [
        SiteRuleSet(
            site_key="bixiange",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "blqudu.cc": [
        SiteRuleSet(
            site_key="blqudu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+_\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.bxwx9.org": [
        SiteRuleSet(
            site_key="bxwx9",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/b/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.ciluke.com": [
        SiteRuleSet(
            site_key="ciluke",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.ciyuanji.com": [
        SiteRuleSet(
            site_key="ciyuanji",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/b_d_(\d+)\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/chapter/(\d+)_\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "czbooks.net": [
        SiteRuleSet(
            site_key="czbooks",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/n/([a-zA-Z0-9]+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.deqixs.com": [
        SiteRuleSet(
            site_key="deqixs",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/xiaoshuo/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "dxmwx.org": [
        SiteRuleSet(
            site_key="dxmwx",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/chapter/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/read/(\d+)_\d+\.html",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.esjzone.cc": [
        SiteRuleSet(
            site_key="esjzone",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/detail/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/forum/(\d+)/\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "fanqienovel.com": [
        SiteRuleSet(
            site_key="fanqienovel",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/page/(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/reader/\d+",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                ),
            ],
        )
    ],
    "www.fsshu.com": [
        SiteRuleSet(
            site_key="fsshu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/biquge/(\d+_\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "b.guidaye.com": [
        SiteRuleSet(
            site_key="guidaye",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.haiwaishubao.com": [
        SiteRuleSet(
            site_key="haiwaishubao",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(?:book|index)/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "hetushu.com": [
        SiteRuleSet(
            site_key="hetushu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "hongxiuzhao.net": [
        SiteRuleSet(
            site_key="hongxiuzhao",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([A-Za-z0-9]+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        ),
    ],
    "www.i25zw.com": [
        SiteRuleSet(
            site_key="i25zw",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/book/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/(\d+)/\d+\.html",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "ixdzs8.com": [
        SiteRuleSet(
            site_key="ixdzs8",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/read/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.jpxs123.com": [
        SiteRuleSet(
            site_key="jpxs123",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/([^/]+)/\d+\.html$",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
                BookIdExtractor(
                    pattern=r"^/([^/]+)/([^.]+)\.html$",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.kadokado.com.tw": [
        SiteRuleSet(
            site_key="kadokado",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/chapter/\d+",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                ),
            ],
        )
    ],
    "www.ktshu.cc": [
        SiteRuleSet(
            site_key="ktshu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.kunnu.com": [
        SiteRuleSet(
            site_key="kunnu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.laoyaoxs.org": [
        SiteRuleSet(
            site_key="laoyaoxs",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/list/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/info/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.lewenn.net": [
        SiteRuleSet(
            site_key="lewenn",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.linovel.net": [
        SiteRuleSet(
            site_key="linovel",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)(?:/|\.html|$)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.linovelib.com": [
        SiteRuleSet(
            site_key="linovelib",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "lnovel.org": [
        SiteRuleSet(
            site_key="lnovel",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/books-(\d+)$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/chapters-\d+",
                    hint="章节 URL 不包含书籍 ID, 请复制小说目录页链接",
                )
            ],
        )
    ],
    "www.mangg.com": [
        SiteRuleSet(
            site_key="mangg_com",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.mangg.net": [
        SiteRuleSet(
            site_key="mangg_net",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.mozishuwu.com": [
        SiteRuleSet(
            site_key="pilibook",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/(\d+)/(?:info|menu|read)",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "8novel.com": [
        SiteRuleSet(
            site_key="n8novel",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novelbooks/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/read/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.8tsw.com": [
        SiteRuleSet(
            site_key="n8tsw",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+_\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.17k.com": [
        SiteRuleSet(
            site_key="n17k",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(?:book|list|chapter)/(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        ),
    ],
    "www.23ddw.net": [
        SiteRuleSet(
            site_key="n23ddw",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/du/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.23qb.com": [
        SiteRuleSet(
            site_key="n23qb",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.37yq.com": [
        SiteRuleSet(
            site_key="n37yq",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/lightnovel/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/lightnovel/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.37yue.com": [
        SiteRuleSet(
            site_key="n37yue",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.69yue.top": [
        SiteRuleSet(
            site_key="n69yue",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/articlecategroy/([^.]+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/mulu\.html$",
                    build_book_id=lambda m: "",
                    pattern_query=r"pid=([A-Za-z0-9]+)",
                    build_book_id_query=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/article/\d+\.html",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页或书籍详情页的链接",
                )
            ],
        )
    ],
    "www.71ge.com": [
        SiteRuleSet(
            site_key="n71ge",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+_\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "101kanshu.com": [
        SiteRuleSet(
            site_key="n101kanshu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)(?:/index)?\.html?$",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/txt/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "novelpia.jp": [
        SiteRuleSet(
            site_key="novelpia",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)(?:/)?$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/viewer/\d+/?$",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                )
            ],
        )
    ],
    "www.piaotia.com": [
        SiteRuleSet(
            site_key="piaotia",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/bookinfo/(\d+)/(\d+)\.html",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
                BookIdExtractor(
                    pattern=r"^/html/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.pilibook.net": [
        SiteRuleSet(
            site_key="pilibook",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/(\d+)/(?:info|menu|read)",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.qbtr.cc": [
        SiteRuleSet(
            site_key="qbtr",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/(\d+)(?:/\d+)?\.html$",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.qidian.com": [
        SiteRuleSet(
            site_key="qidian",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/chapter/(\d+)/\d+/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "book.qq.com": [
        SiteRuleSet(
            site_key="qqbook",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book-detail/(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/book-read/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "quanben5.com": [
        SiteRuleSet(
            site_key="quanben5",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/n/([^/]+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.ruochu.com": [
        SiteRuleSet(
            site_key="ruochu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)(?:/|$)",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/chapter/(\d+)(?:/|$)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "m.sfacg.com": [
        SiteRuleSet(
            site_key="sfacg",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/b/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/i/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/c/\d+/",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页或书籍详情页的链接",
                )
            ],
        )
    ],
    "www.shaoniandream.com": [
        SiteRuleSet(
            site_key="shaoniandream",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book_detail/(\d+)$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/readchapter/\d+$",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                ),
            ],
        )
    ],
    "www.shencou.com": [
        SiteRuleSet(
            site_key="shencou",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/read/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/books/read_\d+\.html$",
                    hint="请在 '详细页面' 内点击 '小说目录' 并复制目录 url",
                )
            ],
        )
    ],
    "www.shu111.com": [
        SiteRuleSet(
            site_key="shu111",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.shuhaige.net": [
        SiteRuleSet(
            site_key="shuhaige",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "ncode.syosetu.com": [
        SiteRuleSet(
            site_key="syosetu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([nN]\w+)/?$",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/([nN]\w+)/\d+/?$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "novel18.syosetu.com": [
        SiteRuleSet(
            site_key="syosetu18",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([nN]\w+)/?$",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/([nN]\w+)/\d+/?$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "syosetu.org": [
        SiteRuleSet(
            site_key="syosetu_org",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)/?$",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)/\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.tongrenquan.org": [
        SiteRuleSet(
            site_key="tongrenquan",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/tongren/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/tongren/(\d+)/\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "tongrenshe.cc": [
        SiteRuleSet(
            site_key="tongrenshe",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/tongren/(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.trxs.cc": [
        SiteRuleSet(
            site_key="trxs",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/tongren/(\d+)\.html",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/tongren/(\d+)/\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "ttkan.co": [
        SiteRuleSet(
            site_key="ttkan",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/chapters/([^/]+)",
                    build_book_id=lambda m: m.group(1),
                ),
                BookIdExtractor(
                    pattern=r"^/novel/pagea/([^_]+)_\d+\.html$",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.uaa.com": [
        SiteRuleSet(
            site_key="uaa",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/intro$",
                    build_book_id=lambda m: "",
                    pattern_query=r"id=(\d+)",
                    build_book_id_query=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/novel/chapter$",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                ),
            ],
        )
    ],
    # "www.wanbengo.com": [SiteRuleSet(
    #     site_key="wanbengo",
    #     extractors=[
    #         BookIdExtractor(
    #             pattern=r"^/(\d+)/",
    #             build_book_id=lambda m: m.group(1),
    #         ),
    #     ],
    #     hints=[],
    # )],
    "www.westnovel.com": [
        SiteRuleSet(
            site_key="westnovel_sub",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([a-z]+)/list/(\d+)\.html$",
                    build_book_id=lambda m: f"{m.group(1)}-list-{m.group(2)}",
                ),
                BookIdExtractor(
                    pattern=r"^/([a-z]+)/zc/(\d+)\.html$",
                    build_book_id=lambda m: f"{m.group(1)}-zc-{m.group(2)}",
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/[a-z]+/showinfo-\d+-\d+-\d+\.html$",
                    hint="章节 URL 不包含书籍 ID, 请复制目录页的链接",
                ),
            ],
        ),
        SiteRuleSet(
            site_key="westnovel",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([a-z]+)/([a-z0-9_]+)/(?:\d+\.html)?$",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        ),
    ],
    "wxsck.com": [
        SiteRuleSet(
            site_key="wxsck",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.xiaoshuoge.info": [
        SiteRuleSet(
            site_key="xiaoshuoge",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/html/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.xiguashuwu.com": [
        SiteRuleSet(
            site_key="xiguashuwu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "m.xs63b.com": [
        SiteRuleSet(
            site_key="xs63b",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/([^/]+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.xshbook.com": [
        SiteRuleSet(
            site_key="xshbook",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/(\d+)/",
                    build_book_id=lambda m: f"{m.group(1)}-{m.group(2)}",
                ),
            ],
            hints=[],
        )
    ],
    "www.yamibo.com": [
        SiteRuleSet(
            site_key="yamibo",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/novel/(\d+)",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/novel/view-chapter",
                    hint="章节 URL 不包含书籍 ID, 请复制小说目录页链接",
                )
            ],
        )
    ],
    "yibige.org": [
        SiteRuleSet(
            site_key="yibige",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.yodu.org": [
        SiteRuleSet(
            site_key="yodu",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/book/(\d+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[],
        )
    ],
    "www.zhenhunxiaoshuo.com": [
        SiteRuleSet(
            site_key="zhenhunxiaoshuo",
            extractors=[
                BookIdExtractor(
                    pattern=r"^/([^/]+)/",
                    build_book_id=lambda m: m.group(1),
                ),
            ],
            hints=[
                HintRule(
                    pattern=r"^/\d+\.html$",
                    hint="章节 URL 不包含书籍 ID, 请复制小说目录页链接",
                )
            ],
        )
    ],
}


def resolve_book_url(url: str) -> BookURLInfo | None:
    """
    Resolve a novel site URL into a standardized BookURLInfo.

      * If a hint rule matches, log the hint and return None.
      * If an extractor matches, return a BookURLInfo dict.

    :param url: URL string.
    :return: BookURLInfo dict or None if unresolved.
    """
    host, path, query = _normalize_host_and_path(url)
    rulesets = SITE_RULES.get(host)
    if not rulesets:
        return None

    for ruleset in rulesets:
        # check hints
        for hint_rule in ruleset.hints:
            if re.search(hint_rule.pattern, path, re.I):
                logger.warning(hint_rule.hint)
                return None

        # check extractors
        for extractor in ruleset.extractors:
            match = re.search(extractor.pattern, path, re.I)
            book_id: str | None = None
            if match:
                book_id = extractor.build_book_id(match)

            if extractor.pattern_query and extractor.build_book_id_query and query:
                match_q = re.search(extractor.pattern_query, query, re.I)
                if match_q:
                    book_id = extractor.build_book_id_query(match_q)

            if book_id:
                return {
                    "book": BookConfig(book_id=book_id),
                    "site_key": ruleset.site_key,
                }

    return None
