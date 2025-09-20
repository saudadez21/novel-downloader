#!/usr/bin/env python3
"""
novel_downloader.web.pages.download
-----------------------------------

"""

from nicegui import ui

from novel_downloader.utils.book_url_resolver import resolve_book_url
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
    # "n8tsw": "笔趣阁 (n8tsw)",
    "n23ddw": "顶点小说网 (n23ddw)",
    "n23qb": "铅笔小说 (n23qb)",
    "n37yq": "三七轻小说 (n37yq)",
    "n37yue": "37阅读网 (n37yue)",
    "n71ge": "新吾爱文学 (n71ge)",
    "piaotia": "飘天文学网 (piaotia)",
    "qbtr": "全本同人小说 (qbtr)",
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
    # "xiaoshuoge": "小说屋 (xiaoshuoge)",
    "xiguashuwu": "西瓜书屋 (xiguashuwu)",
    # "xs63b": "小说路上 (xs63b)",
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

    with ui.card().classes("max-w-[600px] w-full"):
        ui.label("选择输入方式").classes("text-md")

        mode = (
            ui.toggle(
                {"url": "通过 URL", "id": "站点 + ID"},
                value="url",
            )
            .props("dense")
            .classes("w-full")
        )

        url_input = ui.input("小说 URL").props("outlined dense").classes("w-full")
        url_preview = ui.label("").classes("text-sm text-gray-500")

        site = ui.select(
            _SUPPORT_SITES,
            value=_DEFAULT_SITE,
            label="站点",
            with_input=True,
        ).classes("w-full")

        book_id = ui.input("书籍ID").props("outlined dense").classes("w-full")

        def _apply_visibility() -> None:
            is_url = mode.value == "url"
            url_input.visible = is_url
            url_preview.visible = is_url
            site.visible = not is_url
            book_id.visible = not is_url

        mode.on_value_change(lambda e: _apply_visibility())
        _apply_visibility()

        async def _resolve(url: str) -> tuple[str | None, str | None]:
            try:
                info = resolve_book_url(url)
            except Exception:
                return None, None
            if not info:
                return None, None
            site_key = str(info["site_key"])
            bid = str(info["book"]["book_id"])
            return site_key, bid

        add_btn: ui.button | None = None  # forward reference

        async def _add_task_from_url() -> None:
            raw = (url_input.value or "").strip()
            if not raw:
                ui.notify("请输入小说 URL", type="warning")
                return
            site_key, bid = await _resolve(raw)
            if not site_key or not bid:
                ui.notify(
                    "无法解析该 URL, 请确认链接是否正确或该站点是否受支持",
                    type="warning",
                )
                return
            site_display = _SUPPORT_SITES.get(site_key, site_key)
            title = f"{site_display} (id = {bid})"
            ui.notify(f"已添加任务: {title}")
            await manager.add_task(title=title, site=site_key, book_id=bid)

        async def _add_task_from_id() -> None:
            bid = (book_id.value or "").strip()
            if not bid:
                ui.notify("请输入书籍ID", type="warning")
                return
            site_key = str(site.value)
            site_display = _SUPPORT_SITES.get(site_key, site_key)
            title = f"{site_display} (id = {bid})"
            ui.notify(f"已添加任务: {title}")
            await manager.add_task(title=title, site=site_key, book_id=bid)

        async def add_task() -> None:
            # 防抖：禁用按钮
            if add_btn is not None:
                add_btn.props(remove="loading")
                add_btn.props("loading")
                add_btn.disable()
            try:
                if mode.value == "url":
                    await _add_task_from_url()
                else:
                    bid = (book_id.value or "").strip()
                    if bid.startswith("http://") or bid.startswith("https://"):
                        mode.value = "url"
                        _apply_visibility()
                        url_input.value = bid
                        await _add_task_from_url()
                    else:
                        await _add_task_from_id()
            finally:
                if add_btn is not None:
                    add_btn.enable()
                    add_btn.props(remove="loading")

        async def _preview_on_blur() -> None:
            raw = (url_input.value or "").strip()
            if not raw:
                url_preview.text = ""
                return
            site_key, bid = await _resolve(raw)
            if site_key and bid:
                site_display = _SUPPORT_SITES.get(site_key, site_key)
                url_preview.text = f"解析结果：站点 = {site_display}, 书籍ID = {bid}"
            else:
                url_preview.text = "解析失败：该链接可能不受支持或格式不正确"

        url_input.on("blur", _preview_on_blur)

        url_input.on("keydown.enter", lambda e: add_task())
        book_id.on("keydown.enter", lambda e: add_task())

        with ui.row().classes("justify-end w-full"):
            add_btn = ui.button(
                "添加到下载队列",
                on_click=add_task,
                color="primary",
            ).props("unelevated")
