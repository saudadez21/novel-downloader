#!/usr/bin/env python3
"""
novel_downloader.web.pages.download_page
----------------------------------------

"""

from nicegui import ui

import novel_downloader.web.state
from novel_downloader.web.layout import navbar

_SUPPORT_SITES = {
    "qidian": "起点中文网 (qidian)",
    "hetushu": "和图书 (hetushu)",
    "biquge": "笔趣阁 (biquge)",
    "qianbi": "铅笔小说 (qianbi)",
    "piaotia": "飘天文学网 (piaotia)",
    "xiaoshuowu": "小说屋 (xiaoshuowu)",
    "jpxs123": "精品小说网 (jpxs123)",
    "ttkan": "天天看小说 (ttkan)",
    "biquyuedu": "精彩小说 (biquyuedu)",
    "shuhaige": "书海阁小说网 (shuhaige)",
    "ixdzs8": "爱下电子书 (ixdzs8)",
    "xs63b": "小说路上 (xs63b)",
    "dxmwx": "大熊猫文学网 (dxmwx)",
    "yibige": "一笔阁 (yibige)",
    "xshbook": "小说虎 (xshbook)",
    "wanbengo": "完本神站 (wanbengo)",
    "i25zw": "25中文网 (i25zw)",
    "quanben5": "全本小说网 (quanben5)",
    "lewenn": "乐文小说网 (lewenn)",
    "guidaye": "名著阅读 (guidaye)",
    "tongrenquan": "同人圈 (tongrenquan)",
    "qbtr": "全本同人小说 (qbtr)",
    "sfacg": "SF轻小说 (sfacg)",
    "linovelib": "哔哩轻小说 (linovelib)",
    "esjzone": "ESJ Zone (esjzone)",
    "shencou": "神凑轻小说 (shencou)",
    "8novel": "无限轻小说 (8novel)",
    "yamibo": "百合会 (yamibo)",
    "aaatxt": "3A电子书 (aaatxt)",
    "xiguashuwu": "西瓜书屋 (xiguashuwu)",
}
_DEFAULT_SITE = "qidian"


@ui.page("/download")  # type: ignore[misc]
def render() -> None:
    navbar("download")
    ui.label("下载界面").classes("text-lg")

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
            title = f"{site.value} {bid}"
            ui.notify(f"已添加任务：{title}")
            await novel_downloader.web.state.task_manager.add_task(
                title=title, site=str(site.value), book_id=bid
            )

        with ui.row().classes("justify-end w-full"):
            ui.button(
                "添加到下载队列",
                on_click=add_task,
                color="primary",
            ).props("unelevated")
