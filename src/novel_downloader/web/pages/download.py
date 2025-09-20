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


def _chip(text: str) -> None:
    with ui.element("span").classes(
        "inline-flex items-center px-2 py-[2px] text-[11px] rounded bg-grey-2 text-grey-7"  # noqa: E501
    ):
        ui.label(text).classes("leading-none")


@ui.page("/download")  # type: ignore[misc]
def page_download() -> None:
    navbar("download")
    setup_dialog()

    with ui.column().classes("w-full max-w-screen-lg min-w-[320px] mx-auto gap-4"):
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("选择输入方式").classes("text-md")
            # mode toggle on the right
            mode = ui.toggle({"url": "通过 URL", "id": "站点 + ID"}, value="url").props(
                "dense"
            )

        ui.separator()

        # --- URL mode controls ---
        with ui.column().classes("gap-2 w-full") as url_section:
            url_input = (
                ui.input("小说 URL").props("outlined dense clearable").classes("w-full")
            )

            preview_row = ui.row().classes("items-center gap-2 w-full")
            with preview_row:
                _chip("解析结果")
                site_badge = ui.label("").classes("text-xs text-grey-7")
                id_badge = ui.label("").classes("text-xs text-grey-7")
            preview_row.visible = False

            ui.label("粘贴完整的小说详情页链接，系统会自动解析站点和书籍ID").classes(
                "text-xs text-grey-6"
            )  # noqa: E501

        ui.separator()

        # --- Site + ID controls ---
        with ui.column().classes("gap-2 w-full") as site_id_section:
            with ui.row().classes("items-start gap-2 w-full"):
                site = (
                    ui.select(
                        _SUPPORT_SITES,
                        value=_DEFAULT_SITE,
                        label="站点",
                        with_input=True,
                    )
                    .props("outlined dense")
                    .classes("w-full md:w-[40%]")
                )
                book_id = (
                    ui.input("书籍ID")
                    .props("outlined dense clearable")
                    .classes("w-full md:w-[60%]")
                )
            ui.label("若已知站点与书籍ID，可在此直接输入").classes("text-xs text-grey-6")  # noqa: E501

        # Shared actions
        with ui.row().classes("justify-end items-center gap-2 w-full q-mt-sm"):
            clear_btn = ui.button("清空").props("outline")
            add_btn = ui.button("添加到下载队列", color="primary").props("unelevated")

        # ---------- logic ----------

        def _apply_visibility() -> None:
            is_url = mode.value == "url"
            url_section.visible = is_url
            site_id_section.visible = not is_url
            preview_row.visible = (
                is_url and bool(site_badge.text) and bool(id_badge.text)
            )

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

        def _reset_preview() -> None:
            site_badge.text = ""
            id_badge.text = ""
            preview_row.visible = False

        def _clear_all() -> None:
            url_input.value = ""
            book_id.value = ""
            site.value = _DEFAULT_SITE
            _reset_preview()

        mode.on_value_change(lambda _: _apply_visibility())
        _apply_visibility()

        async def _preview_on_blur() -> None:
            raw = (url_input.value or "").strip()
            if not raw:
                _reset_preview()
                return
            site_key, bid = await _resolve(raw)
            if site_key and bid:
                site_display = _SUPPORT_SITES.get(site_key, site_key)
                site_badge.text = f"站点: {site_display}"
                id_badge.text = f"书籍ID: {bid}"
                preview_row.visible = True
            else:
                _reset_preview()
                ui.notify("解析失败：该链接可能不受支持或格式不正确", type="warning")

        url_input.on("blur", _preview_on_blur)

        async def _add_task_from_url() -> None:
            raw = (url_input.value or "").strip()
            if not raw:
                ui.notify("请输入小说 URL", type="warning")
                return
            site_key, bid = await _resolve(raw)
            if not site_key or not bid:
                ui.notify("无法解析该 URL，请检查链接或站点支持情况", type="warning")
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
            # disable button to prevent duplicate submissions
            add_btn.props(remove="loading")
            add_btn.props("loading")
            add_btn.disable()
            try:
                if mode.value == "url":
                    await _add_task_from_url()
                else:
                    # if pasted a URL into ID field
                    bid = (book_id.value or "").strip()
                    if bid.startswith(("http://", "https://")):
                        mode.value = "url"
                        _apply_visibility()
                        url_input.value = bid
                        await _add_task_from_url()
                    else:
                        await _add_task_from_id()
            finally:
                add_btn.enable()
                add_btn.props(remove="loading")

        # enter key submits in both modes
        url_input.on("keydown.enter", lambda _: add_task())
        book_id.on("keydown.enter", lambda _: add_task())

        add_btn.on("click", add_task)
        clear_btn.on("click", lambda: _clear_all())

        # initial state
        _apply_visibility()
