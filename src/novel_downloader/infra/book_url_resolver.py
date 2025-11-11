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
from collections.abc import Callable
from typing import TypedDict, TypeVar
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

BookURLFunc = Callable[[str, str], "BookURLInfo | None"]
E = TypeVar("E", bound=BookURLFunc)
_REGISTRY: dict[str, BookURLFunc] = {}


class BookURLInfo(TypedDict):
    site_key: str
    book_id: str | None
    chapter_id: str | None


def register_extractor(hosts: list[str]) -> Callable[[E], E]:
    def decorator(func: E) -> E:
        for host in hosts:
            _REGISTRY[host] = func
        return func

    return decorator


def _normalize_host_and_path(url: str) -> tuple[str, str, str]:
    """
    Normalize a given URL:
      * Apply HOST_ALIASES mapping to unify different netlocs.
      * Return (canonical_host, path).
    """
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    return parsed.netloc.lower(), parsed.path or "/", parsed.query or ""


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
    if extractor := _REGISTRY.get(host):
        return extractor(path, query)
    return None


@register_extractor(["www.aaatxt.com"])
def extract_aaatxt(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/shu/(\\d+)\\.html$", path):
        return _make_info("aaatxt", m.group(1), None)
    if m := re.search("^/yuedu/(\\d+_\\d+)\\.html$", path):
        return _make_info("aaatxt", m.group(1).split("_")[0], m.group(1))
    return None


@register_extractor(["www.akatsuki-novels.com"])
def extract_akatsuki_novels(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("/stories/view/(\\d+)/novel_id~(\\d+)", path):
        return _make_info("akatsuki_novels", m.group(2), m.group(1))
    if m := re.search("novel_id~(\\d+)", path):
        return _make_info("akatsuki_novels", m.group(1), None)
    return None


@register_extractor(["www.alicesw.com"])
def extract_alicesw(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/([^.]+)\\.html$", path):
        return _make_info("alicesw", None, f"{m.group(1)}-{m.group(2)}")
    if m := re.search("^/novel/(\\d+)\\.html$", path):
        return _make_info("alicesw", m.group(1), None)
    if m := re.search("^/other/chapters/id/(\\d+)\\.html$", path):
        return _make_info("alicesw", m.group(1), None)
    return None


@register_extractor(["www.alphapolis.co.jp"])
def extract_alphapolis(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/novel/(\\d+)/(\\d+)/episode/(\\d+)$", path):
        return _make_info("alphapolis", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/novel/(\\d+)/(\\d+)$", path):
        return _make_info("alphapolis", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.b520.cc"])
def extract_b520(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+_\\d+)/(\\d+)\\.html$", path):
        return _make_info("b520", m.group(1), m.group(2))
    if m := re.search("^/(\\d+_\\d+)/?$", path):
        return _make_info("b520", m.group(1), None)
    return None


@register_extractor(["www.biquge345.com"])
def extract_biquge345(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/chapter/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("biquge345", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/?$", path):
        return _make_info("biquge345", m.group(1), None)
    return None


@register_extractor(["www.biquge5.com"])
def extract_biquge5(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+_\\d+)/(\\d+)\\.html$", path):
        return _make_info("biquge5", m.group(1), m.group(2))
    if m := re.search("^/(\\d+_\\d+)/?$", path):
        return _make_info("biquge5", m.group(1), None)
    return None


@register_extractor(["www.biquguo.com"])
def extract_biquguo(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("biquguo", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/(\\d+)/(\\d+)/?$", path):
        return _make_info("biquguo", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["biquyuedu.com"])
def extract_biquyuedu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/novel/([^/]+)/(\\d+)\\.html$", path):
        return _make_info("biquyuedu", m.group(1), m.group(2))
    if m := re.search("^/novel/([^.]+)\\.html$", path):
        return _make_info("biquyuedu", m.group(1), None)
    return None


@register_extractor(["m.bixiange.me"])
def extract_bixiange(path: str, query: str) -> BookURLInfo | None:
    if m := re.match(r"^/([^/]+)/(\d+)/index/(\d+)\.html$", path):
        cat, bid, chap = m.groups()
        return _make_info("bixiange", f"{cat}-{bid}", chap)
    if m := re.match(r"^/([^/]+)/(\d+)/(\d+)\.html$", path):
        cat, bid, chap = m.groups()
        return _make_info("bixiange", f"{cat}-{bid}", chap)
    if m := re.match(r"^/([^/]+)/(\d+)", path):
        cat, bid = m.groups()
        return _make_info("bixiange", f"{cat}-{bid}", None)
    return None


@register_extractor(["www.blqudu.cc", "www.biqudv.cc"])
def extract_blqudu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+_\\d+)/(\\d+)\\.html$", path):
        return _make_info("blqudu", m.group(1), m.group(2))
    if m := re.search("^/(\\d+_\\d+)/?$", path):
        return _make_info("blqudu", m.group(1), None)
    return None


@register_extractor(["www.bxwx9.org"])
def extract_bxwx9(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/b/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("bxwx9", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/b/(\\d+)/(\\d+)/?$", path):
        return _make_info("bxwx9", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.ciluke.com"])
def extract_ciluke(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("ciluke", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/(\\d+)/(\\d+)/?$", path):
        return _make_info("ciluke", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.ciyuanji.com"])
def extract_ciyuanji(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/chapter/(\\d+)_(\\d+)\\.html$", path):
        return _make_info("ciyuanji", m.group(1), m.group(2))
    if m := re.search("^/b_d_(\\d+)\\.html$", path):
        return _make_info("ciyuanji", m.group(1), None)
    return None


@register_extractor(["czbooks.net"])
def extract_czbooks(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/n/([a-zA-Z0-9]+)/([a-zA-Z0-9]+)", path):
        return _make_info("czbooks", m.group(1), m.group(2))
    if m := re.search("^/n/([a-zA-Z0-9]+)", path):
        return _make_info("czbooks", m.group(1), None)
    return None


@register_extractor(["www.deqixs.com"])
def extract_deqixs(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/xiaoshuo/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("deqixs", m.group(1), m.group(2))
    if m := re.search("^/xiaoshuo/(\\d+)/?$", path):
        return _make_info("deqixs", m.group(1), None)
    return None


@register_extractor(["www.dushu.com"])
def extract_dushu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/showbook/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("dushu", m.group(1), m.group(2))
    if m := re.search("^/showbook/(\\d+)/?$", path):
        return _make_info("dushu", m.group(1), None)
    return None


@register_extractor(["www.dxmwx.org", "tw.dxmwx.org"])
def extract_dxmwx(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/read/(\\d+)_(\\d+)\\.html$", path):
        return _make_info("dxmwx", m.group(1), m.group(2))
    if m := re.search("^/(?:book|chapter)/(\\d+)\\.html$", path):
        return _make_info("dxmwx", m.group(1), None)
    return None


@register_extractor(["www.esjzone.cc"])
def extract_esjzone(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/forum/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("esjzone", m.group(1), m.group(2))
    if m := re.search("^/detail/(\\d+)\\.html$", path):
        return _make_info("esjzone", m.group(1), None)
    return None


@register_extractor(["fanqienovel.com"])
def extract_fanqienovel(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/reader/(\\d+)", path):
        return _make_info("fanqienovel", None, m.group(1))
    if m := re.search("^/page/(\\d+)", path):
        return _make_info("fanqienovel", m.group(1), None)
    return None


@register_extractor(["www.fsshu.com"])
def extract_fsshu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/biquge/(\\d+_\\d+)/([a-zA-Z0-9]+)\\.html$", path):
        return _make_info("fsshu", m.group(1), m.group(2))
    if m := re.search("^/biquge/(\\d+_\\d+)/?$", path):
        return _make_info("fsshu", m.group(1), None)
    return None


@register_extractor(["b.guidaye.com"])
def extract_b(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([^/]+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("guidaye", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/([^/]+)/(\\d+)/?$", path):
        return _make_info("guidaye", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.haiwaishubao.com"])
def extract_haiwaishubao(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(?:book|index)/(\\d+)/(\\d+)(?:_\\d+)?\\.html$", path):
        return _make_info("haiwaishubao", m.group(1), m.group(2))
    if m := re.search("^/(?:book|index)/(\\d+)/", path):
        return _make_info("haiwaishubao", m.group(1), None)
    return None


@register_extractor(["www.hetushu.com", "www.hetubook.com"])
def extract_hetushu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("hetushu", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/", path):
        return _make_info("hetushu", m.group(1), None)
    return None


@register_extractor(["hongxiuzhao.net"])
def extract_hongxiuzhao(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([A-Za-z0-9]+)\\.html$", path):
        return _make_info("hongxiuzhao", m.group(1), None)
    return None


@register_extractor(["www.i25zw.com"])
def extract_i25zw(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("i25zw", m.group(1), m.group(2))
    if m := re.search("^/(?:book/)?(\\d+)\\.html$", path):
        return _make_info("i25zw", m.group(1), None)
    if m := re.search("^/(\\d+)/?$", path):
        return _make_info("i25zw", m.group(1), None)
    return None


@register_extractor(["ixdzs8.com"])
def extract_ixdzs8(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/read/(\\d+)/([a-zA-Z0-9]+)\\.html$", path):
        return _make_info("ixdzs8", m.group(1), m.group(2))
    if m := re.search("^/read/(\\d+)/?$", path):
        return _make_info("ixdzs8", m.group(1), None)
    return None


@register_extractor(["www.jpxs123.com"])
def extract_jpxs123(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([^/]+)/([^/]+)/(\\d+)\\.html$", path):
        return _make_info("jpxs123", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/([^/]+)/([^.]+)\\.html$", path):
        return _make_info("jpxs123", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.kadokado.com.tw"])
def extract_kadokado(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/chapter/(\\d+)", path):
        return _make_info("kadokado", None, m.group(1))
    if m := re.search("^/book/(\\d+)", path):
        return _make_info("kadokado", m.group(1), None)
    return None


@register_extractor(["www.ktshu.cc"])
def extract_ktshu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("ktshu", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/?$", path):
        return _make_info("ktshu", m.group(1), None)
    return None


@register_extractor(["www.kunnu.com"])
def extract_kunnu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([^/]+)/(\\d+)\\.htm$", path):
        return _make_info("kunnu", m.group(1), m.group(2))
    if m := re.search("^/([^/]+)/?$", path):
        return _make_info("kunnu", m.group(1), None)
    return None


@register_extractor(["www.laoyaoxs.org"])
def extract_laoyaoxs(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/list/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("laoyaoxs", m.group(1), m.group(2))
    if m := re.search("^/(?:info|list)/(\\d+)(?:\\.html|/)?$", path):
        return _make_info("laoyaoxs", m.group(1), None)
    return None


@register_extractor(["www.lewenn.net"])
def extract_lewenn(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([^/]+)/(\\d+)\\.html$", path):
        return _make_info("lewenn", m.group(1), m.group(2))
    if m := re.search("^/([^/]+)/?$", path):
        return _make_info("lewenn", m.group(1), None)
    return None


@register_extractor(["www.linovel.net"])
def extract_linovel(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("linovel", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)(?:\\.html|/)?", path):
        return _make_info("linovel", m.group(1), None)
    return None


@register_extractor(["www.linovelib.com"])
def extract_linovelib(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/novel/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("linovelib", m.group(1), m.group(2))
    if m := re.search("^/novel/(\\d+)/vol_\\d+\\.html$", path):
        return _make_info("linovelib", m.group(1), None)
    if m := re.search("^/novel/(\\d+)\\.html$", path):
        return _make_info("linovelib", m.group(1), None)
    return None


@register_extractor(["lnovel.org", "lnovel.tw"])
def extract_lnovel(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/chapters-(\\d+)$", path):
        return _make_info("lnovel", None, m.group(1))
    if m := re.search("^/books-(\\d+)$", path):
        return _make_info("lnovel", m.group(1), None)
    return None


@register_extractor(["www.lvscwx.cc", "www.lvsewx.cc"])
def extract_lvsewx(path: str, query: str) -> BookURLInfo | None:
    if m := re.search(r"^/ebook/(\d+)\.html$", path):
        return _make_info("lvsewx", m.group(1), None)
    if m := re.search(r"^/books/\d+/(\d+)/(\d+)\.html$", path):
        return _make_info("lvsewx", m.group(1), m.group(2))
    return None


@register_extractor(["www.mangg.com"])
def extract_mangg_com(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(id\\d+)/(\\d+)\\.html$", path):
        return _make_info("mangg_com", m.group(1), m.group(2))
    if m := re.search("^/(id\\d+)/?$", path):
        return _make_info("mangg_com", m.group(1), None)
    return None


@register_extractor(["www.mangg.net"])
def extract_mangg_net(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(id\\d+)/(\\d+)\\.html$", path):
        return _make_info("mangg_net", m.group(1), m.group(2))
    if m := re.search("^/(id\\d+)/", path):
        return _make_info("mangg_net", m.group(1), None)
    return None


@register_extractor(["m.mjyhb.com"])
def extract_mjyhb(path: str, query: str) -> BookURLInfo | None:
    if m := re.search(r"^/read_([a-z0-9]+)/([a-z0-9]+)(?:_\d+)?\.html$", path, re.I):
        return _make_info("mjyhb", m.group(1), m.group(2))
    if m := re.search(r"^/info_([a-z0-9]+)/?$", path, re.I):
        return _make_info("mjyhb", m.group(1), None)
    return None


@register_extractor(["101kanshu.com"])
def extract_n101kanshu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/txt/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("n101kanshu", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)(?:/index)?\\.html?$", path):
        return _make_info("n101kanshu", m.group(1), None)
    return None


@register_extractor(["www.17k.com"])
def extract_n17k(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/chapter/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("n17k", m.group(1), m.group(2))
    if m := re.search("^/(?:book|list)/(\\d+)\\.html$", path):
        return _make_info("n17k", m.group(1), None)
    return None


@register_extractor(["www.23ddw.net"])
def extract_n23ddw(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/du/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("n23ddw", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/du/(\\d+)/(\\d+)/?$", path):
        return _make_info("n23ddw", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.23qb.com"])
def extract_n23qb(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("n23qb", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/", path):
        return _make_info("n23qb", m.group(1), None)
    return None


@register_extractor(["www.37yq.com"])
def extract_n37yq(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/lightnovel/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("n37yq", m.group(1), m.group(2))
    if m := re.search("^/lightnovel/(\\d+)(?:\\.html|/catalog)?$", path):
        return _make_info("n37yq", m.group(1), None)
    return None


@register_extractor(["www.37yue.com"])
def extract_n37yue(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("n37yue", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/(\\d+)/(\\d+)/?$", path):
        return _make_info("n37yue", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.69hao.com", "www.69hsw.com"])
def extract_n69hao(path: str, query: str) -> BookURLInfo | None:
    if m := re.search(r"^/(\d+)/(\d+)\.html$", path):
        return _make_info("n69hao", m.group(1), m.group(2))
    if m := re.search(r"^/(\d+)/?$", path):
        return _make_info("n69hao", m.group(1), None)
    return None


@register_extractor(["www.69shuba.com"])
def extract_n69shuba(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/txt/(\\d+)/(\\d+)", path):
        return _make_info("n69shuba", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)(?:\\.htm|/)?$", path):
        return _make_info("n69shuba", m.group(1), None)
    return None


@register_extractor(["www.69yue.top"])
def extract_n69yue(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/article/(\\d+)\\.html$", path):
        return _make_info("n69yue", None, m.group(1))
    if m := re.search("^/articlecategroy/([^.]+)\\.html$", path):
        return _make_info("n69yue", m.group(1), None)
    if (
        path == "/mulu.html"
        and query
        and (mq := re.search("pid=([A-Za-z0-9]+)", query))
    ):
        return _make_info("n69yue", mq.group(1), None)
    return None


@register_extractor(["www.71ge.com"])
def extract_n71ge(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+_\\d+)/(\\d+)\\.html$", path):
        return _make_info("n71ge", m.group(1), m.group(2))
    if m := re.search("^/(\\d+_\\d+)/?$", path):
        return _make_info("n71ge", m.group(1), None)
    return None


@register_extractor(["www.8novel.com", "article.8novel.com"])
def extract_n8novel(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/read/(\\d+)/?$", path):
        if query and (mq := re.search("(\\d+)", query)):
            return _make_info("n8novel", m.group(1), mq.group(1))
        return _make_info("n8novel", m.group(1), None)
    if m := re.search("^/novelbooks/(\\d+)/?$", path):
        return _make_info("n8novel", m.group(1), None)
    return None


@register_extractor(["www.8tsw.com"])
def extract_n8tsw(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+_\\d+)/(\\d+)\\.html$", path):
        return _make_info("n8tsw", m.group(1), m.group(2))
    if m := re.search("^/(\\d+_\\d+)/?$", path):
        return _make_info("n8tsw", m.group(1), None)
    return None


@register_extractor(["novelpia.jp"])
def extract_novelpia(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/viewer/(\\d+)", path):
        return _make_info("novelpia", None, m.group(1))
    if m := re.search("^/novel/(\\d+)", path):
        return _make_info("novelpia", m.group(1), None)
    return None


@register_extractor(["www.piaotia.com"])
def extract_piaotia(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/html/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("piaotia", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/(?:bookinfo|html)/(\\d+)/(\\d+)(?:/|\\.html$)", path):
        return _make_info("piaotia", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.pilibook.net", "www.mozishuwu.com"])
def extract_pilibook(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)/read/(\\d+)\\.html$", path):
        return _make_info("pilibook", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/(\\d+)/(\\d+)/(?:info|menu)(?:/[\\w.-]*)?\\.?html?$", path):
        return _make_info("pilibook", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.qbtr.cc"])
def extract_qbtr(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([^/]+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("qbtr", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/([^/]+)/(\\d+)\\.html$", path):
        return _make_info("qbtr", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.qidian.com"])
def extract_qidian(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/chapter/(\\d+)/(\\d+)/", path):
        return _make_info("qidian", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/", path):
        return _make_info("qidian", m.group(1), None)
    return None


@register_extractor(["book.qq.com"])
def extract_qq(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book-read/(\\d+)/(\\d+)", path):
        return _make_info("qqbook", m.group(1), m.group(2))
    if m := re.search("^/book-detail/(\\d+)", path):
        return _make_info("qqbook", m.group(1), None)
    return None


@register_extractor(["quanben5.com", "big5.quanben5.com"])
def extract_quanben5(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/n/([^/]+)/(\\d+)\\.html$", path):
        return _make_info("quanben5", m.group(1), m.group(2))
    if m := re.search("^/n/([^/]+)/", path):
        return _make_info("quanben5", m.group(1), None)
    return None


@register_extractor(["www.ruochu.com"])
def extract_ruochu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)$", path):
        return _make_info("ruochu", m.group(1), m.group(2))
    if m := re.search("^/(?:book|chapter)/(\\d+)", path):
        return _make_info("ruochu", m.group(1), None)
    return None


@register_extractor(["m.sfacg.com"])
def extract_sfacg(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/c/(\\d+)/", path):
        return _make_info("sfacg", None, m.group(1))
    if m := re.search("^/(?:b|i)/(\\d+)/", path):
        return _make_info("sfacg", m.group(1), None)
    return None


@register_extractor(["www.shaoniandream.com"])
def extract_shaoniandream(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/readchapter/(\\d+)", path):
        return _make_info("shaoniandream", None, m.group(1))
    if m := re.search("^/book_detail/(\\d+)$", path):
        return _make_info("shaoniandream", m.group(1), None)
    return None


@register_extractor(["m.shauthor.com"])
def extract_shauthor(path: str, query: str) -> BookURLInfo | None:
    if m := re.search(r"^/read_([a-z0-9]+)/([a-z0-9]+)(?:_\d+)?\.html$", path, re.I):
        return _make_info("shauthor", m.group(1), m.group(2))
    if m := re.search(r"^/info_([a-z0-9]+)/?$", path, re.I):
        return _make_info("shauthor", m.group(1), None)
    return None


@register_extractor(["www.shencou.com"])
def extract_shencou(path: str, query: str) -> BookURLInfo | None:
    if path.startswith("/books/read_"):
        logger.warning("请在 '详细页面' 内点击 '小说目录'")
        return None
    if m := re.search("^/read/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("shencou", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/read/(\\d+)/(\\d+)/", path):
        return _make_info("shencou", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.shu111.com"])
def extract_shu111(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("shu111", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)\\.html$", path):
        return _make_info("shu111", m.group(1), None)
    return None


@register_extractor(["www.shuhaige.net"])
def extract_shuhaige(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("shuhaige", m.group(1), m.group(2))
    if m := re.search("^/(\\d+)/?$", path):
        return _make_info("shuhaige", m.group(1), None)
    return None


@register_extractor(["ncode.syosetu.com"])
def extract_ncode(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([nN]\\w+)/(\\d+)/?$", path):
        return _make_info("syosetu", m.group(1).lower(), m.group(2))
    if m := re.search("^/([nN]\\w+)/?$", path):
        return _make_info("syosetu", m.group(1).lower(), None)
    return None


@register_extractor(["novel18.syosetu.com"])
def extract_novel18(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([nN]\\w+)/(\\d+)/?$", path):
        return _make_info("syosetu18", m.group(1).lower(), m.group(2))
    if m := re.search("^/([nN]\\w+)/?$", path):
        return _make_info("syosetu18", m.group(1).lower(), None)
    return None


@register_extractor(["syosetu.org"])
def extract_syosetu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/novel/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("syosetu_org", m.group(1), m.group(2))
    if m := re.search("^/novel/(\\d+)/?$", path):
        return _make_info("syosetu_org", m.group(1), None)
    return None


@register_extractor(["www.tianyabooks.com"])
def extract_tianyabooks(path: str, query: str) -> BookURLInfo | None:
    if m := re.match(r"^/([^/]+)/([^/]+)/(\d+)\.html$", path):
        category, book, chap_id = m.groups()
        return _make_info("tianyabooks", f"{category}-{book}", chap_id)
    if m := re.match(r"^/([^/]+)/([^/]+)/?$", path):
        category, book = m.groups()
        return _make_info("tianyabooks", f"{category}-{book}", None)
    return None


@register_extractor(["www.tongrenquan.org"])
def extract_tongrenquan(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/tongren/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("tongrenquan", m.group(1), m.group(2))
    if m := re.search("^/tongren/(\\d+)\\.html$", path):
        return _make_info("tongrenquan", m.group(1), None)
    return None


@register_extractor(["tongrenshe.cc"])
def extract_tongrenshe(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/tongren/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("tongrenshe", m.group(1), m.group(2))
    if m := re.search("^/tongren/(\\d+)\\.html$", path):
        return _make_info("tongrenshe", m.group(1), None)
    return None


@register_extractor(["www.trxs.cc"])
def extract_trxs(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/tongren/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("trxs", m.group(1), m.group(2))
    if m := re.search("^/tongren/(\\d+)\\.html$", path):
        return _make_info("trxs", m.group(1), None)
    return None


@register_extractor(
    [
        "www.ttkan.co",
        "cn.ttkan.co",
        "tw.ttkan.co",
        "www.wa01.com",
        "cn.wa01.com",
        "tw.wa01.com",
    ]
)
def extract_ttkan(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/novel/pagea/([^_]+)_(\\d+)\\.html$", path):
        return _make_info("ttkan", m.group(1), m.group(2))
    if m := re.search("^/novel/chapters/([^/]+)$", path):
        return _make_info("ttkan", m.group(1), None)
    return None


@register_extractor(["twkan.com"])
def extract_twkan(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/txt/(\\d+)/(\\d+)$", path):
        return _make_info("twkan", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)(?:/index\\.html|\\.html)?$", path):
        return _make_info("twkan", m.group(1), None)
    return None


@register_extractor(["www.uaa.com"])
def extract_uaa(path: str, query: str) -> BookURLInfo | None:
    if path == "/novel/chapter" and query and (mq := re.search("id=(\\d+)", query)):
        return _make_info("uaa", None, mq.group(1))
    if path == "/novel/intro" and query and (mq := re.search("id=(\\d+)", query)):
        return _make_info("uaa", mq.group(1), None)
    return None


@register_extractor(["www.wanbengo.com"])
def extract_wanbengo(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("wanbengo", m.group(1), m.group(2))
    if m := re.search("^/(\\d+)/?$", path):
        return _make_info("wanbengo", m.group(1), None)
    return None


@register_extractor(["www.wenku8.net"])
def extract_wenku8(path: str, query: str) -> BookURLInfo | None:
    if path.startswith("/book/"):
        logger.warning("请在 '详细页面' 内点击 '小说目录'")
        return None
    if m := re.search("^/novel/(\\d+)/(\\d+)/(\\d+)\\.htm$", path):
        return _make_info("wenku8", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/novel/(\\d+)/(\\d+)/", path):
        return _make_info("wenku8", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.westnovel.com"])
def extract_westnovel(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([a-z]+)/showinfo-(\\d+-\\d+-\\d+)\\.html$", path):
        return _make_info("westnovel_sub", None, m.group(2))
    if m := re.search("^/([a-z]+)/list/(\\d+)\\.html$", path):
        return _make_info("westnovel_sub", f"{m.group(1)}-list-{m.group(2)}", None)
    if m := re.search("^/([a-z]+)/([a-z0-9_]+)/(\\d+)\\.html$", path):
        return _make_info("westnovel", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/([a-z]+)/([a-z0-9_]+)/?$", path):
        return _make_info("westnovel", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.wxscs.com", "wxscs.com", "wxsck.com"])
def extract_wxscs(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("wxsck", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/?$", path):
        return _make_info("wxsck", m.group(1), None)
    return None


@register_extractor(["www.xiaoshuoge.info"])
def extract_xiaoshuoge(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/html/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("xiaoshuoge", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/html/(\\d+)/(\\d+)/?$", path):
        return _make_info("xiaoshuoge", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.xiguashuwu.com"])
def extract_xiguashuwu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)(?:_\\d+)?\\.html$", path):
        return _make_info("xiguashuwu", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/", path):
        return _make_info("xiguashuwu", m.group(1), None)
    return None


@register_extractor(["m.xs63b.com"])
def extract_xs63b(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/([^/]+)/([^/]+)/(\\d+)\\.html$", path):
        return _make_info("xs63b", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/([^/]+)/([^/]+)/?$", path):
        return _make_info("xs63b", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.xshbook.com"])
def extract_xshbook(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("xshbook", f"{m.group(1)}-{m.group(2)}", m.group(3))
    if m := re.search("^/(\\d+)/(\\d+)/?$", path):
        return _make_info("xshbook", f"{m.group(1)}-{m.group(2)}", None)
    return None


@register_extractor(["www.yamibo.com"])
def extract_yamibo(path: str, query: str) -> BookURLInfo | None:
    if (
        path == "/novel/view-chapter"
        and query
        and (mq := re.search("id=(\\d+)", query))
    ):
        return _make_info("yamibo", None, mq.group(1))
    if m := re.search("^/novel/(\\d+)", path):
        return _make_info("yamibo", m.group(1), None)
    return None


@register_extractor(
    ["www.yibige.org", "sg.yibige.org", "tw.yibige.org", "hk.yibige.org"]
)
def extract_yibige(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("yibige", m.group(1), m.group(2))
    if m := re.search("^/(\\d+)/", path):
        return _make_info("yibige", m.group(1), None)
    return None


@register_extractor(["www.yodu.org"])
def extract_yodu(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/book/(\\d+)/(\\d+)\\.html$", path):
        return _make_info("yodu", m.group(1), m.group(2))
    if m := re.search("^/book/(\\d+)/?$", path):
        return _make_info("yodu", m.group(1), None)
    return None


@register_extractor(["www.zhenhunxiaoshuo.com"])
def extract_zhenhunxiaoshuo(path: str, query: str) -> BookURLInfo | None:
    if m := re.search("^/(\\d+)\\.html$", path):
        return _make_info("zhenhunxiaoshuo", None, m.group(1))
    if m := re.search("^/([^/]+)/?$", path):
        return _make_info("zhenhunxiaoshuo", m.group(1), None)
    return None
