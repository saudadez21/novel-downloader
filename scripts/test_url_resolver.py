#!/usr/bin/env python3
"""
scripts/test_url_resolver.py

Usage:
  # Print mode
  python scripts/test_url_resolver.py

  # Test mode
  python scripts/test_url_resolver.py --test
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from novel_downloader.utils.book_url_resolver import resolve_book_url

_USE_COLOR = sys.stdout.isatty() and os.getenv("NO_COLOR") is None


def _c(txt: str, code: str) -> str:
    if not _USE_COLOR:
        return txt
    return f"\033[{code}m{txt}\033[0m"


def green(txt: str) -> str:
    return _c(txt, "32")


def red(txt: str) -> str:
    return _c(txt, "31")


def yellow(txt: str) -> str:
    return _c(txt, "33")


def bold(txt: str) -> str:
    return _c(txt, "1")


SAMPLES: dict[str, list[tuple[str, str, str | None]]] = {
    # -------------------
    # General fiction
    # -------------------
    "General": [
        # qidian
        ("https://www.qidian.com/book/1010868264/", "qidian", "1010868264"),
        (
            "https://www.qidian.com/chapter/1010868264/405976997/",
            "qidian",
            "1010868264",
        ),
        # qqbook
        ("https://book.qq.com/book-detail/41089201", "qqbook", "41089201"),
        ("https://book.qq.com/book-read/41089201/1", "qqbook", "41089201"),
        # hetushu (+ alias)
        ("https://www.hetushu.com/book/5763/index.html", "hetushu", "5763"),
        ("https://www.hetubook.com/book/5763/4327466.html", "hetushu", "5763"),
        # qianbi
        ("https://www.23qb.net/book/12282/", "qianbi", "12282"),
        ("https://www.23qb.net/book/12282/catalog", "qianbi", "12282"),
        ("https://www.23qb.net/book/12282/7908999.html", "qianbi", "12282"),
        # piaotia
        ("https://www.piaotia.com/bookinfo/13/12345.html", "piaotia", "13-12345"),
        ("https://www.piaotia.com/html/12/12345/index.html", "piaotia", "12-12345"),
        ("https://www.piaotia.com/html/12/12345/114514.html", "piaotia", "12-12345"),
        # n71ge
        ("https://www.71ge.com/65_65536/", "n71ge", "65_65536"),
        ("https://www.71ge.com/65_65536/1.html", "n71ge", "65_65536"),
        # xiaoshuoge
        ("http://www.xiaoshuoge.info/html/987/987654/", "xiaoshuoge", "987-987654"),
        (
            "http://www.xiaoshuoge.info/html/987/987654/123456789.html",
            "xiaoshuoge",
            "987-987654",
        ),
        # jpxs123
        ("https://www.jpxs123.com/xh/zhetian.html", "jpxs123", "xh-zhetian"),
        ("https://www.jpxs123.com/xh/zhetian/1.html", "jpxs123", "xh-zhetian"),
        # ixdzs8
        ("https://ixdzs8.com/read/38804/", "ixdzs8", "38804"),
        ("https://ixdzs8.com/read/38804/p1.html", "ixdzs8", "38804"),
        # xs63b
        (
            "https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/",
            "xs63b",
            "xuanhuan-aoshijiuzhongtian",
        ),
        (
            "https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/8748062.html",
            "xs63b",
            "xuanhuan-aoshijiuzhongtian",
        ),
        # dxmwx (+ alias)
        ("https://www.dxmwx.org/book/55598.html", "dxmwx", "55598"),
        ("https://www.dxmwx.org/chapter/55598.html", "dxmwx", "55598"),
        ("https://www.dxmwx.org/read/55598_47170737.html", "dxmwx", "55598"),
        ("https://tw.dxmwx.org/book/55598.html", "dxmwx", "55598"),
        # wanbengo
        ("https://www.wanbengo.com/1/", "wanbengo", "1"),
        ("https://www.wanbengo.com/1/2.html", "wanbengo", "1"),
        # i25zw
        ("https://www.i25zw.com/book/64371.html", "i25zw", "64371"),
        ("https://www.i25zw.com/64371/", "i25zw", "64371"),
        ("https://www.i25zw.com/64371/153149757.html", "i25zw", "64371"),
        # laoyaoxs
        ("https://www.laoyaoxs.org/info/7359.html", "laoyaoxs", "7359"),
        ("https://www.laoyaoxs.org/list/7359/", "laoyaoxs", "7359"),
        ("https://www.laoyaoxs.org/list/7359/21385.html", "laoyaoxs", "7359"),
        # shu111
        ("https://www.shu111.com/book/282944.html", "shu111", "282944"),
        ("https://www.shu111.com/book/282944/96171674.html", "shu111", "282944"),
        # kunnu
        ("https://www.kunnu.com/guichui/", "kunnu", "guichui"),
        ("https://www.kunnu.com/guichui/27427.htm", "kunnu", "guichui"),
        # quanben5 (+ alias)
        ("https://quanben5.com/n/doushentianxia/", "quanben5", "doushentianxia"),
        (
            "https://quanben5.com/n/doushentianxia/xiaoshuo.html",
            "quanben5",
            "doushentianxia",
        ),
        (
            "https://quanben5.com/n/doushentianxia/13685.html",
            "quanben5",
            "doushentianxia",
        ),
        ("https://big5.quanben5.com/n/doushentianxia/", "quanben5", "doushentianxia"),
        # ttkan (+ aliases / wa01)
        (
            "https://www.ttkan.co/novel/chapters/shengxu-chendong",
            "ttkan",
            "shengxu-chendong",
        ),
        (
            "https://cn.ttkan.co/novel/chapters/shengxu-chendonge",
            "ttkan",
            "shengxu-chendonge",
        ),
        (
            "https://tw.ttkan.co/novel/chapters/shengxu-chendong",
            "ttkan",
            "shengxu-chendong",
        ),
        (
            "https://www.wa01.com/novel/pagea/shengxu-chendong_1.html",
            "ttkan",
            "shengxu-chendong",
        ),
        # guidaye
        ("https://b.guidaye.com/kongbu/654/", "guidaye", "kongbu-654"),
        ("https://b.guidaye.com/kongbu/654/170737.html", "guidaye", "kongbu-654"),
    ],
    # -------------------
    # Biquge-like
    # -------------------
    "Biquge-like": [
        # b520
        ("http://www.b520.cc/8_8187/", "b520", "8_8187"),
        ("http://www.b520.cc/8_8187/3899831.html", "b520", "8_8187"),
        # n8tsw
        ("https://www.8tsw.com/0_1/", "n8tsw", "0_1"),
        ("https://www.8tsw.com/0_1/1.html", "n8tsw", "0_1"),
        # shuhaige
        ("https://www.shuhaige.net/199178/", "shuhaige", "199178"),
        ("https://www.shuhaige.net/199178/86580492.html", "shuhaige", "199178"),
        # xshbook
        ("https://www.xshbook.com/95139/95139418/", "xshbook", "95139-95139418"),
        (
            "https://www.xshbook.com/95139/95139418/407988281.html",
            "xshbook",
            "95139-95139418",
        ),
        # yibige (+ aliases)
        ("https://www.yibige.org/6238/", "yibige", "6238"),
        ("https://www.yibige.org/6238/index.html", "yibige", "6238"),
        ("https://www.yibige.org/6238/1.html", "yibige", "6238"),
        ("https://tw.yibige.org/6238/", "yibige", "6238"),
        ("https://hk.yibige.org/6238/", "yibige", "6238"),
        # lewenn
        ("https://www.lewenn.net/lw1/", "lewenn", "lw1"),
        ("https://www.lewenn.net/lw1/30038546.html", "lewenn", "lw1"),
        # biquyuedu
        ("https://biquyuedu.com/novel/GDr1I1.html", "biquyuedu", "GDr1I1"),
        ("https://biquyuedu.com/novel/GDr1I1/1.html", "biquyuedu", "GDr1I1"),
        # blqudu
        ("https://www.blqudu.cc/137_137144/", "blqudu", "137_137144"),
        ("https://www.biqudv.cc/137_137144/628955328.html", "blqudu", "137_137144"),
        # n23ddw
        ("https://www.23ddw.net/du/80/80892/", "n23ddw", "80-80892"),
        ("https://www.23ddw.net/du/80/80892/13055110.html", "n23ddw", "80-80892"),
        # mangg_com
        ("https://www.mangg.com/id57715/", "mangg_com", "id57715"),
        ("https://www.mangg.com/id57715/632689.html", "mangg_com", "id57715"),
        # mangg_net
        ("https://www.mangg.net/id26581/", "mangg_net", "id26581"),
        ("https://www.mangg.net/id26581/index_2.html", "mangg_net", "id26581"),
        ("https://www.mangg.net/id26581/1159408.html", "mangg_net", "id26581"),
        # fsshu
        ("https://www.fsshu.com/biquge/0_139/", "fsshu", "0_139"),
        ("https://www.fsshu.com/biquge/0_139/c40381.html", "fsshu", "0_139"),
        # biquge5
        ("https://www.biquge5.com/9_9194/", "biquge5", "9_9194"),
        ("https://www.biquge5.com/9_9194/737908.html", "biquge5", "9_9194"),
        # biquguo
        ("https://www.biquguo.com/0/352/", "biquguo", "0-352"),
        ("https://www.biquguo.com/0/352/377618.html", "biquguo", "0-352"),
        # ciluke
        ("https://www.ciluke.com/19/19747/", "ciluke", "19-19747"),
        ("https://www.ciluke.com/19/19747/316194.html", "ciluke", "19-19747"),
        # ktshu
        ("https://www.ktshu.cc/book/47244/", "ktshu", "47244"),
        ("https://www.ktshu.cc/book/47244/418953.html", "ktshu", "47244"),
        # n37yue
        ("https://www.37yue.com/0/180/", "n37yue", "0-180"),
        ("https://www.37yue.com/0/180/164267.html", "n37yue", "0-180"),
        # bxwx9
        ("https://www.bxwx9.org/b/48/48453/", "bxwx9", "48-48453"),
        ("https://www.bxwx9.org/b/48/48453/175908.html", "bxwx9", "48-48453"),
    ],
    # -------------------
    # Doujin
    # -------------------
    "Doujin": [
        # tongrenquan
        ("https://www.tongrenquan.org/tongren/7548.html", "tongrenquan", "7548"),
        ("https://www.tongrenquan.org/tongren/7548/1.html", "tongrenquan", "7548"),
        # trxs
        ("https://www.trxs.cc/tongren/6201.html", "trxs", "6201"),
        ("https://www.trxs.cc/tongren/6201/1.html", "trxs", "6201"),
        # qbtr
        ("https://www.qbtr.cc/tongren/8978.html", "qbtr", "tongren-8978"),
        ("https://www.qbtr.cc/tongren/8978/1.html", "qbtr", "tongren-8978"),
        ("https://www.qbtr.cc/changgui/9089.html", "qbtr", "changgui-9089"),
        ("https://www.qbtr.cc/changgui/9089/1.html", "qbtr", "changgui-9089"),
    ],
    # -------------------
    # Light novel
    # -------------------
    "Light novel": [
        # sfacg (last one is chapter url)
        ("https://m.sfacg.com/b/456123/", "sfacg", "456123"),
        ("https://m.sfacg.com/i/456123/", "sfacg", "456123"),
        ("https://m.sfacg.com/c/5417665/", "sfacg", None),
        # n37yq
        ("https://www.37yq.com/lightnovel/2362.html", "n37yq", "2362"),
        ("https://www.37yq.com/lightnovel/2362/catalog", "n37yq", "2362"),
        ("https://www.37yq.com/lightnovel/2362/92560.html", "n37yq", "2362"),
        # linovelib
        ("https://www.linovelib.com/novel/1234.html", "linovelib", "1234"),
        ("https://www.linovelib.com/novel/1234/47800.html", "linovelib", "1234"),
        ("https://www.linovelib.com/novel/2727.html", "linovelib", "2727"),
        ("https://www.linovelib.com/novel/2727/vol_292741.html", "linovelib", "2727"),
        # n8novel
        ("https://www.8novel.com/novelbooks/3365/", "n8novel", "3365"),
        ("https://article.8novel.com/read/3365/?106235", "n8novel", "3365"),
        ("https://article.8novel.com/read/3365/?106235_2", "n8novel", "3365"),
        # esjzone
        ("https://www.esjzone.cc/detail/1660702902.html", "esjzone", "1660702902"),
        (
            "https://www.esjzone.cc/forum/1660702902/294593.html",
            "esjzone",
            "1660702902",
        ),
        # shencou (first one is a hint page)
        ("https://www.shencou.com/books/read_3540.html", "shencou", None),
        ("https://www.shencou.com/read/3/3540/index.html", "shencou", "3-3540"),
        ("https://www.shencou.com/read/3/3540/156328.html", "shencou", "3-3540"),
        # lnovel (2nd is chapter url)
        ("https://lnovel.org/books-3638", "lnovel", "3638"),
        ("https://lnovel.org/chapters-138730", "lnovel", None),
        ("https://lnovel.tw/books-986", "lnovel", "986"),
        ("https://lnovel.tw/chapters-64989", "lnovel", None),
    ],
    # -------------------
    # Others
    # -------------------
    "Others": [
        # zhenhunxiaoshuo (2nd is chapter url)
        (
            "https://www.zhenhunxiaoshuo.com/modaozushi/",
            "zhenhunxiaoshuo",
            "modaozushi",
        ),
        ("https://www.zhenhunxiaoshuo.com/5419.html", "zhenhunxiaoshuo", None),
        # yamibo (2nd is chapter url)
        ("https://www.yamibo.com/novel/262117", "yamibo", "262117"),
        ("https://www.yamibo.com/novel/view-chapter?id=38772952", "yamibo", None),
        # aaatxt
        ("http://www.aaatxt.com/shu/24514.html", "aaatxt", "24514"),
        ("http://www.aaatxt.com/yuedu/24514_1.html", "aaatxt", "24514"),
        # xiguashuwu
        ("https://www.xiguashuwu.com/book/1234/iszip/1/", "xiguashuwu", "1234"),
        ("https://www.xiguashuwu.com/book/1234/catalog/", "xiguashuwu", "1234"),
        ("https://www.xiguashuwu.com/book/1234/catalog/1.html", "xiguashuwu", "1234"),
        ("https://www.xiguashuwu.com/book/1234/482.html", "xiguashuwu", "1234"),
        ("https://www.xiguashuwu.com/book/1234/482_2.html", "xiguashuwu", "1234"),
        # deqixs
        ("https://www.deqixs.com/xiaoshuo/2026/", "deqixs", "2026"),
        ("https://www.deqixs.com/xiaoshuo/2026/1969933.html", "deqixs", "2026"),
    ],
}


def resolve_book_id(url: str) -> tuple[str | None, str | None]:
    """
    Run resolver and return (site_key|None, book_id|None).
    """
    info = resolve_book_url(url)
    site_key = None if info is None else info["site_key"]
    book_id = None if info is None else info["book"]["book_id"]
    return site_key, book_id


def print_mode(samples: dict[str, list[tuple[str, str, str | None]]]) -> int:
    """Pretty-print parsed results by section."""
    for section, items in samples.items():
        print(bold(f"\n===== {section} ====="))
        for url, _site_key, _expected in items:
            info = resolve_book_url(url)
            print(f"\nURL:    {url}")
            print(f"Parsed: {info}")
    return 0


def test_mode(samples: dict[str, list[tuple[str, str, str | None]]]) -> int:
    """Compare resolver output against expected book_id."""
    total = 0
    mismatches = 0

    for section, items in samples.items():
        print(bold(f"\n===== {section} ====="))
        for url, site_key, book_id in items:
            total += 1
            got_site_key, got_book_id = resolve_book_id(url)

            if got_book_id != book_id:
                mismatches += 1
                print(f"{red('FAIL')} URL: {url}")
                print(f"  expected id:   {book_id}")
                print(f"  got id:        {got_book_id}")
                continue

            if got_book_id and got_site_key != site_key:
                mismatches += 1
                print(f"{red('FAIL')} URL: {url}")
                print(f"  expected site: {site_key}")
                print(f"  got site:      {got_site_key}")
            else:
                print(f"{green('PASS')} URL: {url}")

    print()
    if mismatches == 0:
        print(green(f"All passed: {total} / {total}"))
        return 0
    else:
        print(red(f"Failed: {mismatches} / {total}"))
        return 1


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Test or print results of book URL resolver."
    )
    p.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode.",
    )
    p.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: WARNING).",
    )
    return p


def main() -> int:
    args = build_arg_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s"
    )
    return test_mode(SAMPLES) if args.test else print_mode(SAMPLES)


if __name__ == "__main__":
    raise SystemExit(main())
