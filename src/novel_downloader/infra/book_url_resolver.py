#!/usr/bin/env python3
"""
novel_downloader.infra.book_url_resolver
----------------------------------------

Utility for resolving a novel site URL into a standardized configuration.
"""

from __future__ import annotations

__all__ = ["resolve_book_url"]

import logging
import re
from typing import TypedDict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BookURLInfo(TypedDict):
    site_key: str
    book_id: str | None
    chapter_id: str | None


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
    path = parsed.path or "/"
    query = parsed.query or ""
    return netloc, path, query


def _make_info(
    site_key: str, book_id: str | None, chap_id: str | None = None
) -> BookURLInfo | None:
    return {
        "site_key": site_key,
        "book_id": book_id,
        "chapter_id": chap_id,
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

    match host:
        case "www.aaatxt.com":
            if m := re.search(r"^/shu/(\d+)\.html$", path):
                return _make_info("aaatxt", m.group(1), None)
            if m := re.search(r"^/yuedu/(\d+_\d+)\.html$", path):
                return _make_info("aaatxt", m.group(1).split("_")[0], m.group(1))
            return None

        case "www.akatsuki-novels.com":
            # chapter URLs: /stories/view/<chap_id>/novel_id~<book_id>
            if m := re.search(r"/stories/view/(\d+)/novel_id~(\d+)", path):
                return _make_info("akatsuki_novels", m.group(2), m.group(1))
            # index URLs: /stories/index/novel_id~<book_id>
            if m := re.search(r"novel_id~(\d+)", path):
                return _make_info("akatsuki_novels", m.group(1), None)
            return None

        case "www.alicesw.com":
            # /book/<book_id>/<chapter_token>.html
            if m := re.search(r"^/book/(\d+)/([^.]+)\.html$", path):
                return _make_info("alicesw", None, f"{m.group(1)}-{m.group(2)}")
            if m := re.search(r"^/novel/(\d+)\.html$", path):
                return _make_info("alicesw", m.group(1), None)
            if m := re.search(r"^/other/chapters/id/(\d+)\.html$", path):
                return _make_info("alicesw", m.group(1), None)
            return None

        case "www.alphapolis.co.jp":
            # Chapter URL: /novel/<book_id1>/<book_id2>/episode/<chap_id>
            if m := re.search(r"^/novel/(\d+)/(\d+)/episode/(\d+)$", path):
                return _make_info(
                    "alphapolis", f"{m.group(1)}-{m.group(2)}", m.group(3)
                )
            # Book URL: /novel/<book_id1>/<book_id2>
            if m := re.search(r"^/novel/(\d+)/(\d+)$", path):
                return _make_info("alphapolis", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.b520.cc":
            # chapter: /8_8187/3899831.html
            if m := re.search(r"^/(\d+_\d+)/(\d+)\.html$", path):
                return _make_info("b520", m.group(1), m.group(2))
            # book: /8_8187/
            if m := re.search(r"^/(\d+_\d+)/?$", path):
                return _make_info("b520", m.group(1), None)
            return None

        case "www.biquge345.com":
            # chapter: /chapter/321301/37740966.html
            if m := re.search(r"^/chapter/(\d+)/(\d+)\.html$", path):
                return _make_info("biquge345", m.group(1), m.group(2))
            # book: /book/321301/
            if m := re.search(r"^/book/(\d+)/?$", path):
                return _make_info("biquge345", m.group(1), None)
            return None

        case "www.biquge5.com":
            # chapter: /9_9194/737908.html
            if m := re.search(r"^/(\d+_\d+)/(\d+)\.html$", path):
                return _make_info("biquge5", m.group(1), m.group(2))
            # book: /9_9194/
            if m := re.search(r"^/(\d+_\d+)/?$", path):
                return _make_info("biquge5", m.group(1), None)
            return None

        case "www.biquguo.com":
            # chapter: /0/352/377618.html
            if m := re.search(r"^/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("biquguo", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /0/352/
            if m := re.search(r"^/(\d+)/(\d+)/?$", path):
                return _make_info("biquguo", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "biquyuedu.com":
            # chapter: /novel/GDr1I1/1.html
            if m := re.search(r"^/novel/([^/]+)/(\d+)\.html$", path):
                return _make_info("biquyuedu", m.group(1), m.group(2))
            # book: /novel/GDr1I1.html
            if m := re.search(r"^/novel/([^.]+)\.html$", path):
                return _make_info("biquyuedu", m.group(1), None)
            return None

        case "m.bixiange.me":
            # chapter: /wxxz/20876/index/1.html
            if m := re.search(r"^/([^/]+)/(\d+)/index/(\d+)\.html$", path):
                return _make_info("bixiange", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /wxxz/20876/
            if m := re.search(r"^/([^/]+)/(\d+)/?$", path):
                return _make_info("bixiange", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.blqudu.cc" | "www.biqudv.cc":
            # chapter: /137_137144/628955328.html
            if m := re.search(r"^/(\d+_\d+)/(\d+)\.html$", path):
                return _make_info("blqudu", m.group(1), m.group(2))
            # book: /137_137144/
            if m := re.search(r"^/(\d+_\d+)/?$", path):
                return _make_info("blqudu", m.group(1), None)
            return None

        case "www.bxwx9.org":
            # chapter: /b/48/48453/175908.html
            if m := re.search(r"^/b/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("bxwx9", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /b/48/48453/
            if m := re.search(r"^/b/(\d+)/(\d+)/?$", path):
                return _make_info("bxwx9", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.ciluke.com":
            # chapter: /19/19747/316194.html
            if m := re.search(r"^/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("ciluke", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /19/19747/
            if m := re.search(r"^/(\d+)/(\d+)/?$", path):
                return _make_info("ciluke", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.ciyuanji.com":
            # chapter: /chapter/12030_3046684.html
            if m := re.search(r"^/chapter/(\d+)_(\d+)\.html$", path):
                return _make_info("ciyuanji", m.group(1), m.group(2))
            # book: /b_d_12030.html
            if m := re.search(r"^/b_d_(\d+)\.html$", path):
                return _make_info("ciyuanji", m.group(1), None)
            return None

        case "czbooks.net":
            # chapter: /n/dr4p0k7/drgkg7hgh?chapterNumber=0
            if m := re.search(r"^/n/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)", path):
                return _make_info("czbooks", m.group(1), m.group(2))
            # book: /n/dr4p0k7
            if m := re.search(r"^/n/([a-zA-Z0-9]+)", path):
                return _make_info("czbooks", m.group(1), None)
            return None

        case "www.deqixs.com":
            # chapter: /xiaoshuo/2026/1969933.html
            if m := re.search(r"^/xiaoshuo/(\d+)/(\d+)\.html$", path):
                return _make_info("deqixs", m.group(1), m.group(2))
            # book: /xiaoshuo/2026/
            if m := re.search(r"^/xiaoshuo/(\d+)/?$", path):
                return _make_info("deqixs", m.group(1), None)
            return None

        case "www.dushu.com":
            # chapter: /showbook/138752/1982168.html
            if m := re.search(r"^/showbook/(\d+)/(\d+)\.html$", path):
                return _make_info("dushu", m.group(1), m.group(2))
            # book: /showbook/138752/
            if m := re.search(r"^/showbook/(\d+)/?$", path):
                return _make_info("dushu", m.group(1), None)
            return None

        case "www.dxmwx.org" | "tw.dxmwx.org":
            # chapter: /read/55598_47170737.html
            if m := re.search(r"^/read/(\d+)_(\d+)\.html$", path):
                return _make_info("dxmwx", m.group(1), m.group(2))
            # book: /book/55598.html or /chapter/55598.html
            if m := re.search(r"^/(?:book|chapter)/(\d+)\.html$", path):
                return _make_info("dxmwx", m.group(1), None)
            return None

        case "www.esjzone.cc":
            # chapter: /forum/1660702902/294593.html
            if m := re.search(r"^/forum/(\d+)/(\d+)\.html$", path):
                return _make_info("esjzone", m.group(1), m.group(2))
            # book: /detail/1660702902.html
            if m := re.search(r"^/detail/(\d+)\.html$", path):
                return _make_info("esjzone", m.group(1), None)
            return None

        case "fanqienovel.com":
            # chapter: /reader/<chapter_id>
            if m := re.search(r"^/reader/(\d+)", path):
                return _make_info("fanqienovel", None, m.group(1))
            # book: /page/<book_id>
            if m := re.search(r"^/page/(\d+)", path):
                return _make_info("fanqienovel", m.group(1), None)
            return None

        case "www.fsshu.com":
            # chapter: /biquge/0_139/c40381.html
            if m := re.search(r"^/biquge/(\d+_\d+)/([a-zA-Z0-9]+)\.html$", path):
                return _make_info("fsshu", m.group(1), m.group(2))
            # book: /biquge/0_139/
            if m := re.search(r"^/biquge/(\d+_\d+)/?$", path):
                return _make_info("fsshu", m.group(1), None)
            return None

        case "b.guidaye.com":
            # chapter: /kongbu/654/170737.html
            if m := re.search(r"^/([^/]+)/(\d+)/(\d+)\.html$", path):
                return _make_info("guidaye", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /kongbu/654/
            if m := re.search(r"^/([^/]+)/(\d+)/?$", path):
                return _make_info("guidaye", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.haiwaishubao.com":
            # chapter: /book/102659/5335635.html or /book/102659/5335635_2.html
            if m := re.search(r"^/(?:book|index)/(\d+)/(\d+)(?:_\d+)?\.html$", path):
                return _make_info("haiwaishubao", m.group(1), m.group(2))
            # book: /book/102659/ or /index/102659/ or /index/102659/2/
            if m := re.search(r"^/(?:book|index)/(\d+)/", path):
                return _make_info("haiwaishubao", m.group(1), None)
            return None

        case "www.hetushu.com" | "www.hetubook.com":
            # chapter: /book/5763/4327466.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("hetushu", m.group(1), m.group(2))
            # book: /book/5763/index.html
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("hetushu", m.group(1), None)
            return None

        case "hongxiuzhao.net":
            if m := re.search(r"^/([A-Za-z0-9]+)\.html$", path):
                return _make_info("hongxiuzhao", m.group(1), None)
            return None

        case "www.i25zw.com":
            # chapter: /64371/153149757.html
            if m := re.search(r"^/(\d+)/(\d+)\.html$", path):
                return _make_info("i25zw", m.group(1), m.group(2))
            # book: /book/64371.html or /64371/
            if m := re.search(r"^/(?:book/)?(\d+)\.html$", path):
                return _make_info("i25zw", m.group(1), None)
            if m := re.search(r"^/(\d+)/?$", path):
                return _make_info("i25zw", m.group(1), None)
            return None

        case "ixdzs8.com":
            # chapter: /read/38804/p1.html
            if m := re.search(r"^/read/(\d+)/([a-zA-Z0-9]+)\.html$", path):
                return _make_info("ixdzs8", m.group(1), m.group(2))
            # book: /read/38804/
            if m := re.search(r"^/read/(\d+)/?$", path):
                return _make_info("ixdzs8", m.group(1), None)
            return None

        case "www.jpxs123.com":
            # chapter: /xh/zhetian/1.html
            if m := re.search(r"^/([^/]+)/([^/]+)/(\d+)\.html$", path):
                return _make_info("jpxs123", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /xh/zhetian.html
            if m := re.search(r"^/([^/]+)/([^.]+)\.html$", path):
                return _make_info("jpxs123", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.kadokado.com.tw":
            # chapter: /chapter/3796?titleId=1&ownerId=1
            if m := re.search(r"^/chapter/(\d+)", path):
                return _make_info("kadokado", None, m.group(1))
            # book: /book/1
            if m := re.search(r"^/book/(\d+)", path):
                return _make_info("kadokado", m.group(1), None)
            return None

        case "www.ktshu.cc":
            # chapter: /book/47244/418953.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("ktshu", m.group(1), m.group(2))
            # book: /book/47244/
            if m := re.search(r"^/book/(\d+)/?$", path):
                return _make_info("ktshu", m.group(1), None)
            return None

        case "www.kunnu.com":
            # chapter: /guichui/27427.htm
            if m := re.search(r"^/([^/]+)/(\d+)\.htm$", path):
                return _make_info("kunnu", m.group(1), m.group(2))
            # book: /guichui/
            if m := re.search(r"^/([^/]+)/?$", path):
                return _make_info("kunnu", m.group(1), None)
            return None

        case "www.laoyaoxs.org":
            # chapter: /list/7359/21385.html
            if m := re.search(r"^/list/(\d+)/(\d+)\.html$", path):
                return _make_info("laoyaoxs", m.group(1), m.group(2))
            # book: /info/7359.html or /list/7359/
            if m := re.search(r"^/(?:info|list)/(\d+)(?:\.html|/)?$", path):
                return _make_info("laoyaoxs", m.group(1), None)
            return None

        case "www.lewenn.net":
            # chapter: /lw1/30038546.html
            if m := re.search(r"^/([^/]+)/(\d+)\.html$", path):
                return _make_info("lewenn", m.group(1), m.group(2))
            # book: /lw1/
            if m := re.search(r"^/([^/]+)/?$", path):
                return _make_info("lewenn", m.group(1), None)
            return None

        case "www.linovel.net":
            # chapter: /book/101752/16996.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("linovel", m.group(1), m.group(2))
            # book: /book/101752.html or /book/101752.html#catalog
            if m := re.search(r"^/book/(\d+)(?:\.html|/)?", path):
                return _make_info("linovel", m.group(1), None)
            return None

        case "www.linovelib.com":
            # chapter: /novel/1234/47800.html
            if m := re.search(r"^/novel/(\d+)/(\d+)\.html$", path):
                return _make_info("linovelib", m.group(1), m.group(2))
            # ignore volume index pages like vol_292741.html
            if m := re.search(r"^/novel/(\d+)/vol_\d+\.html$", path):
                return _make_info("linovelib", m.group(1), None)
            # book: /novel/1234.html
            if m := re.search(r"^/novel/(\d+)\.html$", path):
                return _make_info("linovelib", m.group(1), None)
            return None

        case "lnovel.org" | "lnovel.tw":
            # chapter: /chapters-138730
            if m := re.search(r"^/chapters-(\d+)$", path):
                return _make_info("lnovel", None, m.group(1))
            # book: /books-3638
            if m := re.search(r"^/books-(\d+)$", path):
                return _make_info("lnovel", m.group(1), None)
            return None

        case "www.mangg.com":
            # chapter: /id57715/632689.html
            if m := re.search(r"^/(id\d+)/(\d+)\.html$", path):
                return _make_info("mangg_com", m.group(1), m.group(2))
            # book: /id57715/
            if m := re.search(r"^/(id\d+)/?$", path):
                return _make_info("mangg_com", m.group(1), None)
            return None

        case "www.mangg.net":
            # chapter: /id26581/1159408.html
            if m := re.search(r"^/(id\d+)/(\d+)\.html$", path):
                return _make_info("mangg_net", m.group(1), m.group(2))
            # book: /id26581/ or index pages
            if m := re.search(r"^/(id\d+)/", path):
                return _make_info("mangg_net", m.group(1), None)
            return None

        case "101kanshu.com":
            # chapter: /txt/7994/9137080.html
            if m := re.search(r"^/txt/(\d+)/(\d+)\.html$", path):
                return _make_info("n101kanshu", m.group(1), m.group(2))
            # book: /book/7994.html or /book/7994/index.html
            if m := re.search(r"^/book/(\d+)(?:/index)?\.html?$", path):
                return _make_info("n101kanshu", m.group(1), None)
            return None

        case "www.17k.com":
            # chapter: /chapter/3631088/49406153.html
            if m := re.search(r"^/chapter/(\d+)/(\d+)\.html$", path):
                return _make_info("n17k", m.group(1), m.group(2))
            # book: /book/3631088.html or /list/3348757.html
            if m := re.search(r"^/(?:book|list)/(\d+)\.html$", path):
                return _make_info("n17k", m.group(1), None)
            return None

        case "www.23ddw.net":
            # chapter: /du/80/80892/13055110.html
            if m := re.search(r"^/du/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("n23ddw", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /du/80/80892/
            if m := re.search(r"^/du/(\d+)/(\d+)/?$", path):
                return _make_info("n23ddw", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.23qb.com":
            # chapter: /book/12282/7908999.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("n23qb", m.group(1), m.group(2))
            # book: /book/12282/ or /book/12282/catalog
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("n23qb", m.group(1), None)
            return None

        case "www.37yq.com":
            # chapter: /lightnovel/2362/92560.html
            if m := re.search(r"^/lightnovel/(\d+)/(\d+)\.html$", path):
                return _make_info("n37yq", m.group(1), m.group(2))
            # book: /lightnovel/2362.html or /lightnovel/2362/catalog
            if m := re.search(r"^/lightnovel/(\d+)(?:\.html|/catalog)?$", path):
                return _make_info("n37yq", m.group(1), None)
            return None

        case "www.37yue.com":
            # chapter: /0/180/164267.html
            if m := re.search(r"^/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("n37yue", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /0/180/
            if m := re.search(r"^/(\d+)/(\d+)/?$", path):
                return _make_info("n37yue", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.69shuba.com":
            # chapter: /txt/88724/39943182
            if m := re.search(r"^/txt/(\d+)/(\d+)", path):
                return _make_info("n69shuba", m.group(1), m.group(2))
            # book: /book/88724.htm or /book/90442/
            if m := re.search(r"^/book/(\d+)(?:\.htm|/)?$", path):
                return _make_info("n69shuba", m.group(1), None)
            return None

        case "www.69yue.top":
            # chapter: /article/15185363014257741.html
            if m := re.search(r"^/article/(\d+)\.html$", path):
                return _make_info("n69yue", None, m.group(1))
            # book: /articlecategroy/15yu.html or /mulu.html?pid=15yu
            if m := re.search(r"^/articlecategroy/([^.]+)\.html$", path):
                return _make_info("n69yue", m.group(1), None)
            if (
                path == "/mulu.html"
                and query
                and (mq := re.search(r"pid=([A-Za-z0-9]+)", query))
            ):
                return _make_info("n69yue", mq.group(1), None)
            return None

        case "www.71ge.com":
            # chapter: /65_65536/1.html
            if m := re.search(r"^/(\d+_\d+)/(\d+)\.html$", path):
                return _make_info("n71ge", m.group(1), m.group(2))
            # book: /65_65536/
            if m := re.search(r"^/(\d+_\d+)/?$", path):
                return _make_info("n71ge", m.group(1), None)
            return None

        case "www.8novel.com" | "article.8novel.com":
            # chapter: /read/3365/?106235 or ?106235_2
            if m := re.search(r"^/read/(\d+)/?$", path):
                if query and (mq := re.search(r"(\d+)", query)):
                    return _make_info("n8novel", m.group(1), mq.group(1))
                # if query missing, still a valid "book" page
                return _make_info("n8novel", m.group(1), None)
            # book: /novelbooks/3365/
            if m := re.search(r"^/novelbooks/(\d+)/?$", path):
                return _make_info("n8novel", m.group(1), None)
            return None

        case "www.8tsw.com":
            # chapter: /0_1/1.html
            if m := re.search(r"^/(\d+_\d+)/(\d+)\.html$", path):
                return _make_info("n8tsw", m.group(1), m.group(2))
            # book: /0_1/
            if m := re.search(r"^/(\d+_\d+)/?$", path):
                return _make_info("n8tsw", m.group(1), None)
            return None

        case "novelpia.jp":
            # chapter: /viewer/51118
            if m := re.search(r"^/viewer/(\d+)", path):
                return _make_info("novelpia", None, m.group(1))
            # book: /novel/2393 or /novel/2749
            if m := re.search(r"^/novel/(\d+)", path):
                return _make_info("novelpia", m.group(1), None)
            return None

        case "www.piaotia.com":
            # chapter: /html/1/1705/762992.html
            if m := re.search(r"^/html/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("piaotia", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /bookinfo/1/1705.html or /html/1/1705/
            if m := re.search(r"^/(?:bookinfo|html)/(\d+)/(\d+)(?:/|\.html$)", path):
                return _make_info("piaotia", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.pilibook.net" | "www.mozishuwu.com":
            # chapter: /5/16098/read/4249983.html
            if m := re.search(r"^/(\d+)/(\d+)/read/(\d+)\.html$", path):
                return _make_info("pilibook", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /5/16098/info.html or /menu/1.html
            if m := re.search(
                r"^/(\d+)/(\d+)/(?:info|menu)(?:/[\w.-]*)?\.?html?$", path
            ):
                return _make_info("pilibook", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.qbtr.cc":
            # chapter: /tongren/8978/1.html or /changgui/9089/1.html
            if m := re.search(r"^/([^/]+)/(\d+)/(\d+)\.html$", path):
                return _make_info("qbtr", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /tongren/8978.html
            if m := re.search(r"^/([^/]+)/(\d+)\.html$", path):
                return _make_info("qbtr", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.qidian.com":
            # chapter: /chapter/1010868264/405976997/
            if m := re.search(r"^/chapter/(\d+)/(\d+)/", path):
                return _make_info("qidian", m.group(1), m.group(2))
            # book: /book/1010868264/
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("qidian", m.group(1), None)
            return None

        case "book.qq.com":
            # chapter: /book-read/41089201/1
            if m := re.search(r"^/book-read/(\d+)/(\d+)", path):
                return _make_info("qqbook", m.group(1), m.group(2))
            # book: /book-detail/41089201
            if m := re.search(r"^/book-detail/(\d+)", path):
                return _make_info("qqbook", m.group(1), None)
            return None

        case "quanben5.com" | "big5.quanben5.com":
            # chapter: /n/doushentianxia/13685.html
            if m := re.search(r"^/n/([^/]+)/(\d+)\.html$", path):
                return _make_info("quanben5", m.group(1), m.group(2))
            # book: /n/doushentianxia/ or /xiaoshuo.html
            if m := re.search(r"^/n/([^/]+)/", path):
                return _make_info("quanben5", m.group(1), None)
            return None

        case "www.ruochu.com":
            # chapter: /book/158713/13869103
            if m := re.search(r"^/book/(\d+)/(\d+)$", path):
                return _make_info("ruochu", m.group(1), m.group(2))
            # book: /book/158713 or /chapter/158713
            if m := re.search(r"^/(?:book|chapter)/(\d+)", path):
                return _make_info("ruochu", m.group(1), None)
            return None

        case "m.sfacg.com":
            # chapter: /c/5417665/
            if m := re.search(r"^/c/(\d+)/", path):
                return _make_info("sfacg", None, m.group(1))
            # book: /b/456123/ or /i/456123/
            if m := re.search(r"^/(?:b|i)/(\d+)/", path):
                return _make_info("sfacg", m.group(1), None)
            return None

        case "www.shaoniandream.com":
            # chapter: /readchapter/97973
            if m := re.search(r"^/readchapter/(\d+)", path):
                return _make_info("shaoniandream", None, m.group(1))
            # book: /book_detail/754
            if m := re.search(r"^/book_detail/(\d+)$", path):
                return _make_info("shaoniandream", m.group(1), None)
            return None

        case "www.shencou.com":
            # wrong link: /books/read_3540.html
            if path.startswith("/books/read_"):
                logger.warning("请在 '详细页面' 内点击 '小说目录'")
                return None

            # chapter: /read/3/3540/156328.html
            if m := re.search(r"^/read/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("shencou", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /read/3/3540/index.html
            if m := re.search(r"^/read/(\d+)/(\d+)/", path):
                return _make_info("shencou", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.shu111.com":
            # chapter: /book/282944/96171674.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("shu111", m.group(1), m.group(2))
            # book: /book/282944.html
            if m := re.search(r"^/book/(\d+)\.html$", path):
                return _make_info("shu111", m.group(1), None)
            return None

        case "www.shuhaige.net":
            # chapter: /199178/86580492.html
            if m := re.search(r"^/(\d+)/(\d+)\.html$", path):
                return _make_info("shuhaige", m.group(1), m.group(2))
            # book: /199178/
            if m := re.search(r"^/(\d+)/?$", path):
                return _make_info("shuhaige", m.group(1), None)
            return None

        case "ncode.syosetu.com":
            # chapter: /n9584gd/1/
            if m := re.search(r"^/([nN]\w+)/(\d+)/?$", path):
                return _make_info("syosetu", m.group(1).lower(), m.group(2))
            # book: /n9584gd/
            if m := re.search(r"^/([nN]\w+)/?$", path):
                return _make_info("syosetu", m.group(1).lower(), None)
            return None

        case "novel18.syosetu.com":
            # chapter: /n2976io/1/
            if m := re.search(r"^/([nN]\w+)/(\d+)/?$", path):
                return _make_info("syosetu18", m.group(1).lower(), m.group(2))
            # book: /n2976io/
            if m := re.search(r"^/([nN]\w+)/?$", path):
                return _make_info("syosetu18", m.group(1).lower(), None)
            return None

        case "syosetu.org":
            # chapter: /novel/292891/1.html
            if m := re.search(r"^/novel/(\d+)/(\d+)\.html$", path):
                return _make_info("syosetu_org", m.group(1), m.group(2))
            # book: /novel/292891/
            if m := re.search(r"^/novel/(\d+)/?$", path):
                return _make_info("syosetu_org", m.group(1), None)
            return None

        case "www.tongrenquan.org":
            # chapter: /tongren/7548/1.html
            if m := re.search(r"^/tongren/(\d+)/(\d+)\.html$", path):
                return _make_info("tongrenquan", m.group(1), m.group(2))
            # book: /tongren/7548.html
            if m := re.search(r"^/tongren/(\d+)\.html$", path):
                return _make_info("tongrenquan", m.group(1), None)
            return None

        case "tongrenshe.cc":
            # chapter: /tongren/8899/1.html
            if m := re.search(r"^/tongren/(\d+)/(\d+)\.html$", path):
                return _make_info("tongrenshe", m.group(1), m.group(2))
            # book: /tongren/8899.html
            if m := re.search(r"^/tongren/(\d+)\.html$", path):
                return _make_info("tongrenshe", m.group(1), None)
            return None

        case "www.trxs.cc":
            # chapter: /tongren/6201/1.html
            if m := re.search(r"^/tongren/(\d+)/(\d+)\.html$", path):
                return _make_info("trxs", m.group(1), m.group(2))
            # book: /tongren/6201.html
            if m := re.search(r"^/tongren/(\d+)\.html$", path):
                return _make_info("trxs", m.group(1), None)
            return None

        case "www.ttkan.co" | "cn.ttkan.co" | "tw.ttkan.co" | "www.wa01.com" | "cn.wa01.com" | "tw.wa01.com":  # noqa: E501
            # chapter: /novel/pagea/shengxu-chendong_1.html
            if m := re.search(r"^/novel/pagea/([^_]+)_(\d+)\.html$", path):
                return _make_info("ttkan", m.group(1), m.group(2))
            # book: /novel/chapters/shengxu-chendong
            if m := re.search(r"^/novel/chapters/([^/]+)$", path):
                return _make_info("ttkan", m.group(1), None)
            return None

        case "www.uaa.com":
            # chapter: /novel/chapter?id=234639
            if (
                path == "/novel/chapter"
                and query
                and (mq := re.search(r"id=(\d+)", query))
            ):
                return _make_info("uaa", None, mq.group(1))
            # book: /novel/intro?id=11304099
            if (
                path == "/novel/intro"
                and query
                and (mq := re.search(r"id=(\d+)", query))
            ):
                return _make_info("uaa", mq.group(1), None)
            return None

        case "www.wanbengo.com":
            # chapter: /1/2.html
            if m := re.search(r"^/(\d+)/(\d+)\.html$", path):
                return _make_info("wanbengo", m.group(1), m.group(2))
            # book: /1/
            if m := re.search(r"^/(\d+)/?$", path):
                return _make_info("wanbengo", m.group(1), None)
            return None

        case "www.wenku8.net":
            # wrong link: /book/2835.htm
            if path.startswith("/book/"):
                logger.warning("请在 '详细页面' 内点击 '小说目录'")
                return None

            # chapter: /novel/2/2835/113354.htm
            if m := re.search(r"^/novel/(\d+)/(\d+)/(\d+)\.htm$", path):
                return _make_info("wenku8", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /novel/2/2835/index.htm
            if m := re.search(r"^/novel/(\d+)/(\d+)/", path):
                return _make_info("wenku8", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.westnovel.com":
            # chapter (sub site): /q/showinfo-2-40238-0.html
            if m := re.search(r"^/([a-z]+)/showinfo-(\d+-\d+-\d+)\.html$", path):
                return _make_info("westnovel_sub", None, m.group(2))
            # book (sub site): /q/list/725.html
            if m := re.search(r"^/([a-z]+)/list/(\d+)\.html$", path):
                return _make_info(
                    "westnovel_sub", f"{m.group(1)}-list-{m.group(2)}", None
                )
            # main site: /ksl/sq/140072.html
            if m := re.search(r"^/([a-z]+)/([a-z0-9_]+)/(\d+)\.html$", path):
                return _make_info("westnovel", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /ksl/sq/
            if m := re.search(r"^/([a-z]+)/([a-z0-9_]+)/?$", path):
                return _make_info("westnovel", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.wxscs.com" | "wxscs.com" | "wxsck.com":
            # chapter: /book/20297/6660334.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("wxsck", m.group(1), m.group(2))
            # book: /book/20297/
            if m := re.search(r"^/book/(\d+)/?$", path):
                return _make_info("wxsck", m.group(1), None)
            return None

        case "www.xiaoshuoge.info":
            # chapter: /html/987/987654/123456789.html
            if m := re.search(r"^/html/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info(
                    "xiaoshuoge", f"{m.group(1)}-{m.group(2)}", m.group(3)
                )
            # book: /html/987/987654/
            if m := re.search(r"^/html/(\d+)/(\d+)/?$", path):
                return _make_info("xiaoshuoge", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.xiguashuwu.com":
            # chapter: /book/1234/482.html or /book/1234/482_2.html
            if m := re.search(r"^/book/(\d+)/(\d+)(?:_\d+)?\.html$", path):
                return _make_info("xiguashuwu", m.group(1), m.group(2))
            # book: /book/1234/iszip/1/ or /book/1234/catalog/
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("xiguashuwu", m.group(1), None)
            return None

        case "m.xs63b.com":
            # chapter: /xuanhuan/aoshijiuzhongtian/8748062.html
            if m := re.search(r"^/([^/]+)/([^/]+)/(\d+)\.html$", path):
                return _make_info("xs63b", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /xuanhuan/aoshijiuzhongtian/
            if m := re.search(r"^/([^/]+)/([^/]+)/?$", path):
                return _make_info("xs63b", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.xshbook.com":
            # chapter: /95139/95139418/407988281.html
            if m := re.search(r"^/(\d+)/(\d+)/(\d+)\.html$", path):
                return _make_info("xshbook", f"{m.group(1)}-{m.group(2)}", m.group(3))
            # book: /95139/95139418/
            if m := re.search(r"^/(\d+)/(\d+)/?$", path):
                return _make_info("xshbook", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.yamibo.com":
            # chapter: /novel/view-chapter?id=38772952
            if (
                path == "/novel/view-chapter"
                and query
                and (mq := re.search(r"id=(\d+)", query))
            ):
                return _make_info("yamibo", None, mq.group(1))
            # book: /novel/262117
            if m := re.search(r"^/novel/(\d+)", path):
                return _make_info("yamibo", m.group(1), None)
            return None

        case "www.yibige.org" | "sg.yibige.org" | "tw.yibige.org" | "hk.yibige.org":
            # chapter: /6238/1.html
            if m := re.search(r"^/(\d+)/(\d+)\.html$", path):
                return _make_info("yibige", m.group(1), m.group(2))
            # book: /6238/ or /6238/index.html
            if m := re.search(r"^/(\d+)/", path):
                return _make_info("yibige", m.group(1), None)
            return None

        case "www.yodu.org":
            # chapter: /book/18862/4662939.html
            if m := re.search(r"^/book/(\d+)/(\d+)\.html$", path):
                return _make_info("yodu", m.group(1), m.group(2))
            # book: /book/18862/
            if m := re.search(r"^/book/(\d+)/?$", path):
                return _make_info("yodu", m.group(1), None)
            return None

        case "www.zhenhunxiaoshuo.com":
            # chapter: /5419.html
            if m := re.search(r"^/(\d+)\.html$", path):
                return _make_info("zhenhunxiaoshuo", None, m.group(1))
            # book: /modaozushi/
            if m := re.search(r"^/([^/]+)/?$", path):
                return _make_info("zhenhunxiaoshuo", m.group(1), None)
            return None

        case _:
            return None
