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

from novel_downloader.schemas import BookConfig

logger = logging.getLogger(__name__)


class BookURLInfo(TypedDict):
    book: BookConfig
    site_key: str


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
    site_key: str, book_id: str | None, chap_id: str | None
) -> BookURLInfo | None:
    if book_id is None:
        return None
    return {"book": BookConfig(book_id=book_id), "site_key": site_key}


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
            if m := re.search(r"^/shu/(\d+)\.html", path):
                return _make_info("aaatxt", m.group(1), None)
            if m := re.search(r"^/yuedu/(\d+)_\d+\.html", path):
                return _make_info("aaatxt", m.group(1), None)
            return None

        case "www.akatsuki-novels.com":
            if m := re.search(r"novel_id~(\d+)", path):
                return _make_info("akatsuki_novels", m.group(1), None)
            return None

        case "www.alicesw.com":
            if path.startswith("/book/"):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if m := re.search(r"^/novel/(\d+)\.html$", path):
                return _make_info("alicesw", m.group(1), None)
            if m := re.search(r"^/other/chapters/id/(\d+)\.html$", path):
                return _make_info("alicesw", m.group(1), None)
            return None

        case "www.alphapolis.co.jp":
            if m := re.search(r"^/novel/(\d+)/(\d+)", path):
                return _make_info("alphapolis", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.b520.cc":
            if m := re.search(r"^/(\d+_\d+)/", path):
                return _make_info("b520", m.group(1), None)
            return None

        case "www.biquge345.com":
            if m := re.search(r"^/(?:book|chapter)/(\d+)/", path):
                return _make_info("biquge345", m.group(1), None)
            return None

        case "www.biquge5.com":
            if m := re.search(r"^/(\d+_\d+)/", path):
                return _make_info("biquge5", m.group(1), None)
            return None

        case "www.biquguo.com":
            if m := re.search(r"^/(\d+)/(\d+)/", path):
                return _make_info("biquguo", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "biquyuedu.com":
            if m := re.search(r"^/novel/([^/]+)/\d+\.html$", path):
                return _make_info("biquyuedu", m.group(1), None)
            if m := re.search(r"^/novel/([^.]+)\.html", path):
                return _make_info("biquyuedu", m.group(1), None)
            return None

        case "m.bixiange.me":
            if m := re.search(r"^/([^/]+)/(\d+)/", path):
                return _make_info("bixiange", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.blqudu.cc" | "www.biqudv.cc":
            if m := re.search(r"^/(\d+_\d+)/", path):
                return _make_info("blqudu", m.group(1), None)
            return None

        case "www.bxwx9.org":
            if m := re.search(r"^/b/(\d+)/(\d+)/", path):
                return _make_info("bxwx9", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.ciluke.com":
            if m := re.search(r"^/(\d+)/(\d+)/", path):
                return _make_info("ciluke", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.ciyuanji.com":
            if m := re.search(r"^/b_d_(\d+)\.html$", path):
                return _make_info("ciyuanji", m.group(1), None)
            if m := re.search(r"^/chapter/(\d+)_\d+\.html$", path):
                return _make_info("ciyuanji", m.group(1), None)
            return None

        case "czbooks.net":
            if m := re.search(r"^/n/([a-zA-Z0-9]+)", path):
                return _make_info("czbooks", m.group(1), None)
            return None

        case "www.deqixs.com":
            if m := re.search(r"^/xiaoshuo/(\d+)/", path):
                return _make_info("deqixs", m.group(1), None)
            return None

        case "www.dushu.com":
            if m := re.search(r"^/showbook/(\d+)/", path):
                return _make_info("dushu", m.group(1), None)
            if m := re.search(r"^/showbook/(\d+)/\d+\.html", path):
                return _make_info("dushu", m.group(1), None)
            return None

        case "www.dxmwx.org" | "tw.dxmwx.org":
            if m := re.search(r"^/book/(\d+)\.html", path):
                return _make_info("dxmwx", m.group(1), None)
            if m := re.search(r"^/chapter/(\d+)\.html", path):
                return _make_info("dxmwx", m.group(1), None)
            if m := re.search(r"^/read/(\d+)_\d+\.html", path):
                return _make_info("dxmwx", m.group(1), None)
            return None

        case "www.esjzone.cc":
            if m := re.search(r"^/detail/(\d+)\.html", path):
                return _make_info("esjzone", m.group(1), None)
            if m := re.search(r"^/forum/(\d+)/\d+\.html$", path):
                return _make_info("esjzone", m.group(1), None)
            return None

        case "fanqienovel.com":
            if re.search(r"^/reader/\d+", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if m := re.search(r"^/page/(\d+)", path):
                return _make_info("fanqienovel", m.group(1), None)
            return None

        case "www.fsshu.com":
            if m := re.search(r"^/biquge/(\d+_\d+)/", path):
                return _make_info("fsshu", m.group(1), None)
            return None

        case "b.guidaye.com":
            if m := re.search(r"^/([^/]+)/(\d+)/", path):
                return _make_info("guidaye", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.haiwaishubao.com":
            if m := re.search(r"^/(?:book|index)/(\d+)/", path):
                return _make_info("haiwaishubao", m.group(1), None)
            return None

        case "www.hetushu.com" | "www.hetubook.com":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("hetushu", m.group(1), None)
            return None

        case "hongxiuzhao.net":
            if m := re.search(r"^/([A-Za-z0-9]+)\.html", path):
                return _make_info("hongxiuzhao", m.group(1), None)
            return None

        case "www.i25zw.com":
            if m := re.search(r"^/(\d+)/", path):
                return _make_info("i25zw", m.group(1), None)
            if m := re.search(r"^/book/(\d+)\.html", path):
                return _make_info("i25zw", m.group(1), None)
            if m := re.search(r"^/(\d+)/\d+\.html", path):
                return _make_info("i25zw", m.group(1), None)
            return None

        case "ixdzs8.com":
            if m := re.search(r"^/read/(\d+)/", path):
                return _make_info("ixdzs8", m.group(1), None)
            return None

        case "www.jpxs123.com":
            if m := re.search(r"^/([^/]+)/([^/]+)/\d+\.html$", path):
                return _make_info("jpxs123", f"{m.group(1)}-{m.group(2)}", None)
            if m := re.search(r"^/([^/]+)/([^.]+)\.html$", path):
                return _make_info("jpxs123", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.kadokado.com.tw":
            if re.search(r"^/chapter/\d+", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if m := re.search(r"^/book/(\d+)", path):
                return _make_info("kadokado", m.group(1), None)
            return None

        case "www.ktshu.cc":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("ktshu", m.group(1), None)
            return None

        case "www.kunnu.com":
            if m := re.search(r"^/([^/]+)/", path):
                return _make_info("kunnu", m.group(1), None)
            return None

        case "www.laoyaoxs.org":
            if m := re.search(r"^/list/(\d+)/", path):
                return _make_info("laoyaoxs", m.group(1), None)
            if m := re.search(r"^/info/(\d+)\.html", path):
                return _make_info("laoyaoxs", m.group(1), None)
            return None

        case "www.lewenn.net":
            if m := re.search(r"^/([^/]+)/", path):
                return _make_info("lewenn", m.group(1), None)
            return None

        case "www.linovel.net":
            if m := re.search(r"^/book/(\d+)(?:/|\.html|$)", path):
                return _make_info("linovel", m.group(1), None)
            return None

        case "www.linovelib.com":
            if m := re.search(r"^/novel/(\d+)\.html", path):
                return _make_info("linovelib", m.group(1), None)
            if m := re.search(r"^/novel/(\d+)/", path):
                return _make_info("linovelib", m.group(1), None)
            return None

        case "lnovel.org" | "lnovel.tw":
            if re.search(r"^/chapters-\d+", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制小说目录页链接")
                return None

            if m := re.search(r"^/books-(\d+)$", path):
                return _make_info("lnovel", m.group(1), None)
            return None

        case "www.mangg.com":
            if m := re.search(r"^/([^/]+)/", path):
                return _make_info("mangg_com", m.group(1), None)
            return None

        case "www.mangg.net":
            if m := re.search(r"^/([^/]+)/", path):
                return _make_info("mangg_net", m.group(1), None)
            return None

        case "101kanshu.com":
            if m := re.search(r"^/book/(\d+)(?:/index)?\.html?$", path):
                return _make_info("n101kanshu", m.group(1), None)
            if m := re.search(r"^/txt/(\d+)/", path):
                return _make_info("n101kanshu", m.group(1), None)
            return None

        case "www.17k.com":
            if m := re.search(r"^/(?:book|list|chapter)/(\d+)", path):
                return _make_info("n17k", m.group(1), None)
            return None

        case "www.23ddw.net":
            if m := re.search(r"^/du/(\d+)/(\d+)/", path):
                return _make_info("n23ddw", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.23qb.com":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("n23qb", m.group(1), None)
            return None

        case "www.37yq.com":
            if m := re.search(r"^/lightnovel/(\d+)\.html", path):
                return _make_info("n37yq", m.group(1), None)
            if m := re.search(r"^/lightnovel/(\d+)/", path):
                return _make_info("n37yq", m.group(1), None)
            return None

        case "www.37yue.com":
            if m := re.search(r"^/(\d+)/(\d+)/", path):
                return _make_info("n37yue", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.69shuba.com":
            if m := re.search(r"^/(?:book|txt)/(\d+)", path):
                return _make_info("n69shuba", m.group(1), None)
            return None

        case "www.69yue.top":
            if re.search(r"^/article/\d+\.html", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页或书籍详情页的链接")
                return None

            if m := re.search(r"^/articlecategroy/([^.]+)\.html", path):
                return _make_info("n69yue", m.group(1), None)
            if (
                path == "/mulu.html"
                and query
                and (mq := re.search(r"pid=([A-Za-z0-9]+)", query))
            ):
                return _make_info("n69yue", mq.group(1), None)
            return None

        case "www.71ge.com":
            if m := re.search(r"^/(\d+_\d+)/", path):
                return _make_info("n71ge", m.group(1), None)
            return None

        case "www.8novel.com" | "article.8novel.com":
            if m := re.search(r"^/novelbooks/(\d+)/", path):
                return _make_info("n8novel", m.group(1), None)
            if m := re.search(r"^/read/(\d+)/", path):
                return _make_info("n8novel", m.group(1), None)
            return None

        case "www.8tsw.com":
            if m := re.search(r"^/(\d+_\d+)/", path):
                return _make_info("n8tsw", m.group(1), None)
            return None

        case "novelpia.jp":
            if path.startswith("/viewer/"):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if m := re.search(r"^/novel/(\d+)(?:/)?$", path):
                return _make_info("novelpia", m.group(1), None)
            return None

        case "www.piaotia.com":
            if m := re.search(r"^/bookinfo/(\d+)/(\d+)\.html", path):
                return _make_info("piaotia", f"{m.group(1)}-{m.group(2)}", None)
            if m := re.search(r"^/html/(\d+)/(\d+)/", path):
                return _make_info("piaotia", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.pilibook.net" | "www.mozishuwu.com":
            if m := re.search(r"^/(\d+)/(\d+)/(?:info|menu|read)", path):
                return _make_info("pilibook", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.qbtr.cc":
            if m := re.search(r"^/([^/]+)/(\d+)(?:/\d+)?\.html$", path):
                return _make_info("qbtr", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.qidian.com":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("qidian", m.group(1), None)
            if m := re.search(r"^/chapter/(\d+)/\d+/", path):
                return _make_info("qidian", m.group(1), None)
            return None

        case "book.qq.com":
            if m := re.search(r"^/book-detail/(\d+)", path):
                return _make_info("qqbook", m.group(1), None)
            if m := re.search(r"^/book-read/(\d+)/", path):
                return _make_info("qqbook", m.group(1), None)
            return None

        case "quanben5.com" | "big5.quanben5.com":
            if m := re.search(r"^/n/([^/]+)/", path):
                return _make_info("quanben5", m.group(1), None)
            return None

        case "www.ruochu.com":
            if m := re.search(r"^/book/(\d+)(?:/|$)", path):
                return _make_info("ruochu", m.group(1), None)
            if m := re.search(r"^/chapter/(\d+)(?:/|$)", path):
                return _make_info("ruochu", m.group(1), None)
            return None

        case "m.sfacg.com":
            if re.search(r"^/c/\d+/", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页或书籍详情页的链接")
                return None

            if m := re.search(r"^/b/(\d+)/", path):
                return _make_info("sfacg", m.group(1), None)
            if m := re.search(r"^/i/(\d+)/", path):
                return _make_info("sfacg", m.group(1), None)
            return None

        case "www.shaoniandream.com":
            if path.startswith("/readchapter/"):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if m := re.search(r"^/book_detail/(\d+)$", path):
                return _make_info("shaoniandream", m.group(1), None)
            return None

        case "www.shencou.com":
            if path.startswith("/books/read_"):
                logger.warning("请在 '详细页面' 内点击 '小说目录' 并复制目录 url")
                return None

            if m := re.search(r"^/read/(\d+)/(\d+)/", path):
                return _make_info("shencou", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.shu111.com":
            if m := re.search(r"^/book/(\d+)\.html", path):
                return _make_info("shu111", m.group(1), None)
            if m := re.search(r"^/book/(\d+)/\d+\.html$", path):
                return _make_info("shu111", m.group(1), None)
            return None

        case "www.shuhaige.net":
            if m := re.search(r"^/(\d+)/", path):
                return _make_info("shuhaige", m.group(1), None)
            return None

        case "ncode.syosetu.com":
            if m := re.search(r"^/([nN]\w+)/?$", path):
                return _make_info("syosetu", m.group(1), None)
            if m := re.search(r"^/([nN]\w+)/\d+/?$", path):
                return _make_info("syosetu", m.group(1), None)
            return None

        case "novel18.syosetu.com":
            if m := re.search(r"^/([nN]\w+)/?$", path):
                return _make_info("syosetu18", m.group(1), None)
            if m := re.search(r"^/([nN]\w+)/\d+/?$", path):
                return _make_info("syosetu18", m.group(1), None)
            return None

        case "syosetu.org":
            if m := re.search(r"^/novel/(\d+)/?$", path):
                return _make_info("syosetu_org", m.group(1), None)
            if m := re.search(r"^/novel/(\d+)/\d+\.html$", path):
                return _make_info("syosetu_org", m.group(1), None)
            return None

        case "www.tongrenquan.org":
            if m := re.search(r"^/tongren/(\d+)\.html", path):
                return _make_info("tongrenquan", m.group(1), None)
            if m := re.search(r"^/tongren/(\d+)/\d+\.html$", path):
                return _make_info("tongrenquan", m.group(1), None)
            return None

        case "tongrenshe.cc":
            if m := re.search(r"^/tongren/(\d+)", path):
                return _make_info("tongrenshe", m.group(1), None)
            return None

        case "www.trxs.cc":
            if m := re.search(r"^/tongren/(\d+)\.html", path):
                return _make_info("trxs", m.group(1), None)
            if m := re.search(r"^/tongren/(\d+)/\d+\.html$", path):
                return _make_info("trxs", m.group(1), None)
            return None

        case "www.ttkan.co" | "cn.ttkan.co" | "tw.ttkan.co" | "www.wa01.com" | "cn.wa01.com" | "tw.wa01.com":  # noqa: E501
            if m := re.search(r"^/novel/chapters/([^/]+)", path):
                return _make_info("ttkan", m.group(1), None)
            if m := re.search(r"^/novel/pagea/([^_]+)_\d+\.html$", path):
                return _make_info("ttkan", m.group(1), None)
            return None

        case "www.uaa.com":
            if path == "/novel/chapter":
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if (
                path == "/novel/intro"
                and query
                and (mq := re.search(r"id=(\d+)", query))
            ):
                return _make_info("uaa", mq.group(1), None)
            return None

        case "www.wanbengo.com":
            if m := re.search(r"^/(\d+)/", path):
                return _make_info("wanbengo", m.group(1), None)
            return None

        case "www.wenku8.net":
            if path.startswith("/book/"):
                logger.warning("请在 '详细页面' 内点击 '小说目录'")
                return None

            if m := re.search(r"^/novel/(\d+)/(\d+)/", path):
                return _make_info("wenku8", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.westnovel.com":
            if re.search(r"^/[a-z]+/showinfo-\d+-\d+-\d+\.html$", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制目录页的链接")
                return None

            if m := re.search(r"^/([a-z]+)/list/(\d+)\.html$", path):
                return _make_info(
                    "westnovel_sub", f"{m.group(1)}-list-{m.group(2)}", None
                )
            if m := re.search(r"^/([a-z]+)/zc/(\d+)\.html$", path):
                return _make_info(
                    "westnovel_sub", f"{m.group(1)}-zc-{m.group(2)}", None
                )
            if m := re.search(r"^/([a-z]+)/([a-z0-9_]+)/(?:\d+\.html)?$", path):
                return _make_info("westnovel", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.wxscs.com" | "wxscs.com" | "wxsck.com":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("wxsck", m.group(1), None)
            return None

        case "www.xiaoshuoge.info":
            if m := re.search(r"^/html/(\d+)/(\d+)/", path):
                return _make_info("xiaoshuoge", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.xiguashuwu.com":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("xiguashuwu", m.group(1), None)
            return None

        case "m.xs63b.com":
            if m := re.search(r"^/([^/]+)/([^/]+)/", path):
                return _make_info("xs63b", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.xshbook.com":
            if m := re.search(r"^/(\d+)/(\d+)/", path):
                return _make_info("xshbook", f"{m.group(1)}-{m.group(2)}", None)
            return None

        case "www.yamibo.com":
            if re.search(r"^/novel/view-chapter", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制小说目录页链接")
                return None

            if m := re.search(r"^/novel/(\d+)", path):
                return _make_info("yamibo", m.group(1), None)
            return None

        case "www.yibige.org" | "sg.yibige.org" | "tw.yibige.org" | "hk.yibige.org":
            if m := re.search(r"^/(\d+)/", path):
                return _make_info("yibige", m.group(1), None)
            return None

        case "www.yodu.org":
            if m := re.search(r"^/book/(\d+)/", path):
                return _make_info("yodu", m.group(1), None)
            return None

        case "www.zhenhunxiaoshuo.com":
            if re.search(r"^/\d+\.html$", path):
                logger.warning("章节 URL 不包含书籍 ID, 请复制小说目录页链接")
                return None

            if m := re.search(r"^/([^/]+)/", path):
                return _make_info("zhenhunxiaoshuo", m.group(1), None)
            return None

        case _:
            return None
