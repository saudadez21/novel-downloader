import logging

import pytest
from novel_downloader.libs.book_url_resolver import resolve_book_url

# fmt: off
CASES_SUCCESS = [
    # (url, expected_site_key, expected_book_id)
    # qidian
    ("https://www.qidian.com/book/1010868264/", "qidian", "1010868264"),
    ("https://www.qidian.com/chapter/1010868264/405976997/", "qidian","1010868264"),
    # qqbook
    ("https://book.qq.com/book-detail/41089201", "qqbook", "41089201"),
    ("https://book.qq.com/book-read/41089201/1", "qqbook", "41089201"),
    # ciyuanji
    ("https://www.ciyuanji.com/b_d_12030.html", "ciyuanji", "12030"),
    ("https://www.ciyuanji.com/chapter/12030_3046684.html", "ciyuanji", "12030"),
    # hetushu (+ alias)
    ("https://www.hetushu.com/book/5763/index.html", "hetushu", "5763"),
    ("https://www.hetubook.com/book/5763/4327466.html", "hetushu", "5763"),
    # n23qb
    ("https://www.23qb.com/book/12282/", "n23qb", "12282"),
    ("https://www.23qb.com/book/12282/catalog", "n23qb", "12282"),
    ("https://www.23qb.com/book/12282/7908999.html", "n23qb", "12282"),
    # yodu
    ("https://www.yodu.org/book/18862/", "yodu", "18862"),
    ("https://www.yodu.org/book/18862/4662939.html", "yodu", "18862"),
    # piaotia
    ("https://www.piaotia.com/bookinfo/13/12345.html", "piaotia", "13-12345"),
    ("https://www.piaotia.com/html/12/12345/index.html", "piaotia", "12-12345"),
    ("https://www.piaotia.com/html/12/12345/114514.html", "piaotia", "12-12345"),
    # n71ge
    ("https://www.71ge.com/65_65536/", "n71ge", "65_65536"),
    ("https://www.71ge.com/65_65536/1.html", "n71ge", "65_65536"),
    # xiaoshuoge
    ("http://www.xiaoshuoge.info/html/987/987654/", "xiaoshuoge", "987-987654"),
    ("http://www.xiaoshuoge.info/html/987/987654/123456789.html", "xiaoshuoge", "987-987654"),  # noqa: E501
    # jpxs123
    ("https://www.jpxs123.com/xh/zhetian.html", "jpxs123", "xh-zhetian"),
    ("https://www.jpxs123.com/xh/zhetian/1.html", "jpxs123", "xh-zhetian"),
    # ixdzs8
    ("https://ixdzs8.com/read/38804/", "ixdzs8", "38804"),
    ("https://ixdzs8.com/read/38804/p1.html", "ixdzs8", "38804"),
    # xs63b
    ("https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/", "xs63b", "xuanhuan-aoshijiuzhongtian"),  # noqa: E501
    ("https://m.xs63b.com/xuanhuan/aoshijiuzhongtian/8748062.html", "xs63b", "xuanhuan-aoshijiuzhongtian"),  # noqa: E501
    # dxmwx (+ alias)
    ("https://www.dxmwx.org/book/55598.html", "dxmwx", "55598"),
    ("https://www.dxmwx.org/chapter/55598.html", "dxmwx", "55598"),
    ("https://www.dxmwx.org/read/55598_47170737.html", "dxmwx", "55598"),
    ("https://tw.dxmwx.org/book/55598.html", "dxmwx", "55598"),
    # wanbengo
    # ("https://www.wanbengo.com/1/", "wanbengo", "1"),
    # ("https://www.wanbengo.com/1/2.html", "wanbengo", "1"),
    # i25zw
    ("https://www.i25zw.com/book/64371.html", "i25zw", "64371"),
    ("https://www.i25zw.com/64371/", "i25zw", "64371"),
    ("https://www.i25zw.com/64371/153149757.html", "i25zw", "64371"),
    # n69yue
    ("https://www.69yue.top/articlecategroy/15yu.html", "n69yue", "15yu"),
    ("https://www.69yue.top/mulu.html?pid=15yu", "n69yue", "15yu"),
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
    ("https://quanben5.com/n/doushentianxia/xiaoshuo.html", "quanben5", "doushentianxia"),  # noqa: E501
    ("https://quanben5.com/n/doushentianxia/13685.html", "quanben5", "doushentianxia"),
    ("https://big5.quanben5.com/n/doushentianxia/", "quanben5", "doushentianxia"),
    # ttkan (+ aliases / wa01)
    ("https://www.ttkan.co/novel/chapters/shengxu-chendong", "ttkan", "shengxu-chendong"),  # noqa: E501
    ("https://cn.ttkan.co/novel/chapters/shengxu-chendonge", "ttkan", "shengxu-chendonge"),  # noqa: E501
    ("https://tw.ttkan.co/novel/chapters/shengxu-chendong", "ttkan", "shengxu-chendong"),  # noqa: E501
    ("https://www.wa01.com/novel/pagea/shengxu-chendong_1.html", "ttkan", "shengxu-chendong"),  # noqa: E501
    # guidaye
    ("https://b.guidaye.com/kongbu/654/", "guidaye", "kongbu-654"),
    ("https://b.guidaye.com/kongbu/654/170737.html", "guidaye", "kongbu-654"),
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
    ("https://www.xshbook.com/95139/95139418/407988281.html", "xshbook", "95139-95139418"),  # noqa: E501
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
    # ("https://biquyuedu.com/novel/GDr1I1.html", "biquyuedu", "GDr1I1"),
    # ("https://biquyuedu.com/novel/GDr1I1/1.html", "biquyuedu", "GDr1I1"),
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
    # sfacg
    ("https://m.sfacg.com/b/456123/", "sfacg", "456123"),
    ("https://m.sfacg.com/i/456123/", "sfacg", "456123"),
    # n37yq
    ("https://www.37yq.com/lightnovel/2362.html", "n37yq", "2362"),
    ("https://www.37yq.com/lightnovel/2362/catalog", "n37yq", "2362"),
    ("https://www.37yq.com/lightnovel/2362/92560.html", "n37yq", "2362"),
    # westnovel
    ("https://www.westnovel.com/ksl/sq/", "westnovel", "ksl-sq"),
    ("https://www.westnovel.com/ksl/sq/140072.html", "westnovel", "ksl-sq"),
    # westnovel_sub
    ("https://www.westnovel.com/q/list/908.html", "westnovel_sub", "q-list-908"),
    # n101kanshu
    ("https://101kanshu.com/book/7994.html", "n101kanshu", "7994"),
    ("https://101kanshu.com/book/7994/index.html", "n101kanshu", "7994"),
    ("https://101kanshu.com/txt/7994/9137080.html", "n101kanshu", "7994"),
    # linovelib
    ("https://www.linovelib.com/novel/1234.html", "linovelib", "1234"),
    ("https://www.linovelib.com/novel/1234/47800.html", "linovelib", "1234"),
    ("https://www.linovelib.com/novel/2727.html", "linovelib", "2727"),
    ("https://www.linovelib.com/novel/2727/vol_292741.html", "linovelib", "2727"),
    # linovel
    ("https://www.linovel.net/book/101752.html", "linovel", "101752"),
    ("https://www.linovel.net/book/101752.html#catalog", "linovel", "101752"),
    ("https://www.linovel.net/book/101752/16996.html", "linovel", "101752"),
    # n8novel
    ("https://www.8novel.com/novelbooks/3365/", "n8novel", "3365"),
    ("https://article.8novel.com/read/3365/?106235", "n8novel", "3365"),
    ("https://article.8novel.com/read/3365/?106235_2", "n8novel", "3365"),
    # esjzone
    ("https://www.esjzone.cc/detail/1660702902.html", "esjzone", "1660702902"),
    ("https://www.esjzone.cc/forum/1660702902/294593.html", "esjzone", "1660702902"),
    # shencou
    ("https://www.shencou.com/read/3/3540/index.html", "shencou", "3-3540"),
    ("https://www.shencou.com/read/3/3540/156328.html", "shencou", "3-3540"),
    # lnovel
    ("https://lnovel.org/books-3638", "lnovel", "3638"),
    ("https://lnovel.tw/books-986", "lnovel", "986"),
    # zhenhunxiaoshuo
    ("https://www.zhenhunxiaoshuo.com/modaozushi/", "zhenhunxiaoshuo", "modaozushi"),
    # yamibo
    ("https://www.yamibo.com/novel/262117", "yamibo", "262117"),
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
    # syosetu
    ("https://ncode.syosetu.com/n9584gd/", "syosetu", "n9584gd"),
    ("https://ncode.syosetu.com/n9584gd/1/", "syosetu", "n9584gd"),
    ("https://ncode.syosetu.com/n4826lc/", "syosetu", "n4826lc"),
    ("https://ncode.syosetu.com/n4826lc/1/", "syosetu", "n4826lc"),
    # syosetu18
    ("https://novel18.syosetu.com/n2976io/", "syosetu18", "n2976io"),
    ("https://novel18.syosetu.com/n2976io/1/", "syosetu18", "n2976io"),
    ("https://novel18.syosetu.com/n8543hb/", "syosetu18", "n8543hb"),
    ("https://novel18.syosetu.com/n8543hb/1/", "syosetu18", "n8543hb"),
    # syosetu_org
    ("https://syosetu.org/novel/292891/", "syosetu_org", "292891"),
    ("https://syosetu.org/novel/292891/1.html", "syosetu_org", "292891"),
    # akatsuki_novels
    ("https://www.akatsuki-novels.com/stories/index/novel_id~103", "akatsuki_novels", "103"),  # noqa: E501
    ("https://www.akatsuki-novels.com/stories/view/163722/novel_id~103", "akatsuki_novels", "103"),  # noqa: E501
    # alphapolis
    ("https://www.alphapolis.co.jp/novel/547686423/112003230", "alphapolis", "547686423-112003230"),  # noqa: E501
    ("https://www.alphapolis.co.jp/novel/547686423/112003230/episode/10322710", "alphapolis", "547686423-112003230"),  # noqa: E501
    # novelpia
    ("https://novelpia.jp/novel/2393?sid=main5", "novelpia", "2393"),
    ("https://novelpia.jp/novel/2749", "novelpia", "2749"),
    # pilibook
    ("https://www.pilibook.net/1/627/info.html", "pilibook", "1-627"),
    ("https://www.pilibook.net/1/627/menu/1.html", "pilibook", "1-627"),
    ("https://www.pilibook.net/1/627/read/247250.html", "pilibook", "1-627"),
    ("https://www.mozishuwu.com/1/627/info.html", "pilibook", "1-627"),
    ("https://www.mozishuwu.com/1/627/menu/1.html", "pilibook", "1-627"),
    ("https://www.mozishuwu.com/1/627/read/247250.html", "pilibook", "1-627"),
    # alicesw
    ("https://www.alicesw.com/novel/46857.html", "alicesw", "46857"),
    ("https://www.alicesw.com/other/chapters/id/46857.html", "alicesw", "46857"),
    # haiwaishubao
    ("https://www.haiwaishubao.com/book/102659/", "haiwaishubao", "102659"),
    ("https://www.haiwaishubao.com/index/102659/", "haiwaishubao", "102659"),
    ("https://www.haiwaishubao.com/index/102659/2/", "haiwaishubao", "102659"),
    ("https://www.haiwaishubao.com/book/102659/5335635.html", "haiwaishubao", "102659"),
    ("https://www.haiwaishubao.com/book/102659/5335635_2.html", "haiwaishubao", "102659"),  # noqa: E501
    # hongxiuzhao
    ("https://hongxiuzhao.net/VPGlv8.html", "hongxiuzhao", "VPGlv8"),
    # uaa
    ("https://www.uaa.com/novel/intro?id=869062931097194496", "uaa", "869062931097194496"),  # noqa: E501
    # czbooks
    ("https://czbooks.net/n/dr4p0k7", "czbooks", "dr4p0k7"),
    ("https://czbooks.net/n/dr4p0k7/drgkg7hgh?chapterNumber=0", "czbooks", "dr4p0k7"),
    # bixiange
    ("https://m.bixiange.me/wxxz/20876/", "bixiange", "wxxz-20876"),
    ("https://m.bixiange.me/wxxz/20876/index/1.html", "bixiange", "wxxz-20876"),
    # tongrenshe
    ("https://tongrenshe.cc/tongren/8899.html", "tongrenshe", "8899"),
    ("https://tongrenshe.cc/tongren/8899/1.html", "tongrenshe", "8899"),
    # wxsck
    ("https://wxsck.com/book/20297/", "wxsck", "20297"),
    ("https://wxsck.com/book/20297/6660334.html", "wxsck", "20297"),
    ("https://www.wxscs.com/book/20297/", "wxsck", "20297"),
    ("https://www.wxscs.com/book/20297/6660334.html", "wxsck", "20297"),
    # biquge345
    ("https://www.biquge345.com/book/321301/", "biquge345", "321301"),
    ("https://www.biquge345.com/chapter/321301/37740966.html", "biquge345", "321301"),
    # n17k
    ("https://www.17k.com/book/3348757.html", "n17k", "3348757"),
    ("https://www.17k.com/list/3348757.html", "n17k", "3348757"),
    ("https://www.17k.com/chapter/3348757/44541132.html", "n17k", "3348757"),
]

CASES_HINT = [
    # (url, expected_hint_substring)
    (
        "https://www.69yue.top/article/15185363014257741.html",
        "章节 URL 不包含书籍 ID, 请复制目录页或书籍详情页的链接",
    ),
    (
        "https://m.sfacg.com/c/5417665/",
        "章节 URL 不包含书籍 ID, 请复制目录页或书籍详情页的链接",
    ),
    (
        "https://www.shencou.com/books/read_3540.html",
        "请在 '详细页面' 内点击 '小说目录'",
    ),
    (
        "https://lnovel.org/chapters-138730",
        "章节 URL 不包含书籍 ID, 请复制小说目录页链接",
    ),
    (
        "https://lnovel.tw/chapters-64989",
        "章节 URL 不包含书籍 ID, 请复制小说目录页链接",
    ),
    (
        "https://www.zhenhunxiaoshuo.com/5419.html",
        "章节 URL 不包含书籍 ID, 请复制小说目录页链接",
    ),
    (
        "https://www.yamibo.com/novel/view-chapter?id=38772952",
        "章节 URL 不包含书籍 ID, 请复制小说目录页链接",
    ),
    (
        "https://www.westnovel.com/q/showinfo-2-48701-0.html",
        "章节 URL 不包含书籍 ID, 请复制目录页的链接",
    ),
    (
        "https://novelpia.jp/viewer/51118",
        "章节 URL 不包含书籍 ID, 请复制目录页的链接",
    ),
    (
        "https://www.alicesw.com/book/48247/563ed665333ad.html",
        "章节 URL 不包含书籍 ID, 请复制目录页的链接",
    ),
    (
        "https://www.uaa.com/novel/chapter?id=869062931193663489",
        "章节 URL 不包含书籍 ID, 请复制目录页的链接",
    ),
]

CASES_INVALID = [
    # URLs with no rule should return None
    "https://www.unknownsite.com/book/123.html",
    "not a url",
    "",
]
# fmt: on


@pytest.mark.parametrize("url,site_key,book_id", CASES_SUCCESS)
def test_resolver_extracts_expected_ids(url: str, site_key: str, book_id: str):
    """Ensure resolve_book_url() extracts correct site_key and book_id."""
    result = resolve_book_url(url)
    assert result is not None, f"{url}: expected BookURLInfo, got None"
    assert result["site_key"] == site_key
    assert result["book"].book_id == book_id


@pytest.mark.parametrize("url,expected_hint", CASES_HINT)
def test_resolver_logs_hint_and_returns_none(
    url: str, expected_hint: str, caplog: pytest.LogCaptureFixture
):
    """Ensure hint URLs log warning and return None."""
    caplog.set_level(logging.WARNING)
    result = resolve_book_url(url)
    assert result is None, f"{url}: should return None for hint URLs"
    # verify that hint text was logged
    assert any(
        expected_hint in msg for msg in caplog.messages
    ), f"{url}: expected hint '{expected_hint}' not found in logs"


@pytest.mark.parametrize("url", CASES_INVALID)
def test_resolver_handles_invalid_urls(url: str):
    """Unrecognized or invalid URLs should safely return None."""
    result = resolve_book_url(url)
    assert result is None, f"{url}: expected None for invalid URL"
