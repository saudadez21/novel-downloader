#!/usr/bin/env python3
"""
novel_downloader.web.pages.download
-----------------------------------

"""

from nicegui import ui

from novel_downloader.web.components import navbar
from novel_downloader.web.services import manager, setup_dialog

_SUPPORT_SITES = {
    "aaatxt": "3A电子书 (aaatxt)",
    "b520": "笔趣阁 (b520)",
    "biquge5": "笔趣阁 (biquge5)",
    "biquguo": "笔趣阁小说网 (biquguo)",
    "biquyuedu": "精彩小说 (biquyuedu)",
    "blqudu": "笔趣读 (blqudu)",
    "bxwx9": "笔下文学网 (bxwx9)",
    "ciluke": "思路客 (ciluke)",
    "dxmwx": "大熊猫文学网 (dxmwx)",
    "esjzone": "ESJ Zone (esjzone)",
    "fsshu": "笔趣阁 (fsshu)",
    "guidaye": "名著阅读 (guidaye)",
    "hetushu": "和图书 (hetushu)",
    "i25zw": "25中文网 (i25zw)",
    "ixdzs8": "爱下电子书 (ixdzs8)",
    "jpxs123": "精品小说网 (jpxs123)",
    "ktshu": "八一中文网 (ktshu)",
    "kunnu": "鲲弩小说 (kunnu)",
    "laoyaoxs": "老幺小说网 (laoyaoxs)",
    "lewenn": "乐文小说网 (lewenn)",
    "linovelib": "哔哩轻小说 (linovelib)",
    "lnovel": "轻小说百科 (lnovel)",
    "mangg_com": "追书网.com (mangg_com)",
    "mangg_net": "追书网.net (mangg_net)",
    "n8novel": "无限轻小说 (n8novel)",
    "n8tsw": "笔趣阁 (n8tsw)",
    "n23ddw": "顶点小说网 (n23ddw)",
    "n37yq": "三七轻小说 (n37yq)",
    "n37yue": "37阅读网 (n37yue)",
    "n71ge": "新吾爱文学 (n71ge)",
    "piaotia": "飘天文学网 (piaotia)",
    "qbtr": "全本同人小说 (qbtr)",
    "qianbi": "铅笔小说 (qianbi)",
    "qidian": "起点中文网 (qidian)",
    "qqbook": "QQ阅读 (qqbook)",
    "quanben5": "全本小说网 (quanben5)",
    "sfacg": "SF轻小说 (sfacg)",
    "shencou": "神凑轻小说 (shencou)",
    "shu111": "书林文学 (shu111)",
    "shuhaige": "书海阁小说网 (shuhaige)",
    "tongrenquan": "同人圈 (tongrenquan)",
    "trxs": "同人小说网 (trxs)",
    "ttkan": "天天看小说 (ttkan)",
    "wanbengo": "完本神站 (wanbengo)",
    "xiaoshuowu": "小说屋 (xiaoshuowu)",
    "xiguashuwu": "西瓜书屋 (xiguashuwu)",
    "xs63b": "小说路上 (xs63b)",
    "xshbook": "小说虎 (xshbook)",
    "yamibo": "百合会 (yamibo)",
    "yibige": "一笔阁 (yibige)",
    "yodu": "有度中文网 (yodu)",
    "zhenhunxiaoshuo": "镇魂小说网 (zhenhunxiaoshuo)",
}
_DEFAULT_SITE = "qidian"


@ui.page("/download")  # type: ignore[misc]
def page_download() -> None:
    navbar("download")
    ui.label("下载界面").classes("text-lg")
    setup_dialog()

    with ui.card().classes("max-w-[600px]"):
        site = ui.select(
            _SUPPORT_SITES,
            value=_DEFAULT_SITE,
            label="站点",
            with_input=True,
        ).classes("w-full")

        book_id = ui.input("书籍ID").props("outlined dense").classes("w-full")

        async def add_task() -> None:
            bid = (book_id.value or "").strip()
            if not bid:
                ui.notify("请输入书籍ID", type="warning")
                return
            title = f"{site.value} (id = {bid})"
            ui.notify(f"已添加任务: {title}")
            await manager.add_task(title=title, site=str(site.value), book_id=bid)

        with ui.row().classes("justify-end w-full"):
            ui.button(
                "添加到下载队列",
                on_click=add_task,
                color="primary",
            ).props("unelevated")
