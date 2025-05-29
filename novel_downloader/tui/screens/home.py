#!/usr/bin/env python3
"""
novel_downloader.tui.screens
----------------------------

"""

import logging

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, RichLog, Select, Static

from novel_downloader.tui.widgets.richlog_handler import RichLogHandler


class HomeScreen(Screen):  # type: ignore[misc]
    CSS_PATH = "../styles/home_layout.tcss"

    def compose(self) -> ComposeResult:
        yield Vertical(
            self._make_title_bar(),
            self._make_input_row(),
            RichLog(id="log", highlight=True, markup=False),
            id="main-layout",
        )

    def on_mount(self) -> None:
        log_widget = self.query_one("#log", RichLog)

        handler = RichLogHandler(log_widget)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit":
            logging.info("退出应用")
            self.app.exit()

        elif event.button.id == "settings":
            logging.info("设置功能暂未实现")

        elif event.button.id == "download":
            site = self.query_one("#site", Select).value
            ids = self.query_one("#book_ids", Input).value
            if not site or not ids.strip():
                logging.warning("请填写完整信息")
            else:
                id_list = [x.strip() for x in ids.split(",") if x.strip()]
                logging.info(f"下载请求: {site} | {id_list}")

    def _make_title_bar(self) -> Horizontal:
        return Horizontal(
            Static("小说下载器", id="title"),
            Button("设置", id="settings"),
            Button("关闭", id="exit"),
            id="title-bar",
        )

    def _make_input_row(self) -> Horizontal:
        return Horizontal(
            Vertical(self._make_site_select(), classes="left"),
            Vertical(
                Input(placeholder="输入书籍ID (支持逗号分隔)", id="book_ids"),
                classes="middle",
            ),
            Vertical(Button("下载", id="download"), classes="right"),
            id="input-row",
        )

    def _make_site_select(self) -> Select:
        return Select(
            options=[
                ("起点中文网", "qidian"),
                ("笔趣阁", "biquge"),
                ("铅笔小说", "qianbi"),
                ("SF轻小说", "sfacg"),
                ("ESJ Zone", "esjzone"),
                ("百合会", "yamibo"),
                ("哔哩轻小说", "linovelib"),
            ],
            prompt="选择站点",
            value="qidian",
            id="site",
        )
