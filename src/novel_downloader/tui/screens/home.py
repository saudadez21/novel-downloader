#!/usr/bin/env python3
"""
novel_downloader.tui.screens.home
---------------------------------

"""

import asyncio
import logging
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, ProgressBar, RichLog, Select, Static

from novel_downloader.config import ConfigAdapter
from novel_downloader.core.factory import (
    get_downloader,
    get_exporter,
    get_fetcher,
    get_parser,
)
from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import LoginField
from novel_downloader.tui.widgets.richlog_handler import RichLogHandler
from novel_downloader.utils.i18n import t


class HomeScreen(Screen):  # type: ignore[misc]
    CSS_PATH = "../styles/home_layout.tcss"

    def compose(self) -> ComposeResult:
        yield Vertical(
            self._make_title_bar(),
            self._make_input_row(),
            ProgressBar(id="prog", name="下载进度"),
            Static("下载进度: 0/0 章", id="label-progress"),
            RichLog(id="log", highlight=True, markup=False),
            id="main-layout",
        )

    def on_mount(self) -> None:
        log_widget = self.query_one("#log", RichLog)

        self._log_handler = RichLogHandler(log_widget)
        self._log_handler.setLevel(logging.INFO)
        self._log_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        self._setup_logging(self._log_handler)

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
                return
            id_list = {x.strip() for x in ids.split(",") if x.strip()}
            adapter = ConfigAdapter(config=self.app.config, site=str(site))
            # asyncio.create_task(self._download(adapter, str(site), id_list))
            self.run_worker(
                self._download(adapter, str(site), id_list),
                name="download",
                group="downloads",
                description="正在下载书籍...",
            )

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

    async def _download(
        self,
        adapter: ConfigAdapter,
        site: str,
        book_ids: set[str],
    ) -> None:
        btn = self.query_one("#download", Button)
        btn.disabled = True
        try:
            logging.info(f"下载请求: {site} | {book_ids}")
            downloader_cfg = adapter.get_downloader_config()
            fetcher_cfg = adapter.get_fetcher_config()
            parser_cfg = adapter.get_parser_config()
            exporter_cfg = adapter.get_exporter_config()

            parser = get_parser(site, parser_cfg)
            exporter = get_exporter(site, exporter_cfg)
            self._setup_logging(self._log_handler)

            async with get_fetcher(site, fetcher_cfg) as fetcher:
                if downloader_cfg.login_required and not await fetcher.load_state():
                    login_data = await self._prompt_login_fields(
                        fetcher, fetcher.login_fields, downloader_cfg
                    )
                    if not await fetcher.login(**login_data):
                        logging.info(t("download_login_failed"))
                        return
                    await fetcher.save_state()

                downloader = get_downloader(
                    fetcher=fetcher,
                    parser=parser,
                    site=site,
                    config=downloader_cfg,
                )

                for book_id in book_ids:
                    logging.info(t("download_downloading", book_id=book_id, site=site))
                    await downloader.download(
                        {"book_id": book_id},
                        progress_hook=self._update_progress,
                    )
                    await asyncio.to_thread(exporter.export, book_id)

                if downloader_cfg.login_required and fetcher.is_logged_in:
                    await fetcher.save_state()
        finally:
            btn.disabled = False

    async def _prompt_login_fields(
        self,
        fetcher: FetcherProtocol,
        fields: list[LoginField],
        cfg: Any = None,
    ) -> dict[str, Any]:
        """
        Push a LoginScreen to collect all required fields,
        then return the dict of values when the user submits.
        """
        # cfg_dict = asdict(cfg) if cfg else {}
        # login_screen = LoginScreen(fields, cfg_dict)
        # await self.app.push_screen(login_screen)
        # await self.app.pop_screen()
        return {}

    def _setup_logging(self, handler: logging.Handler) -> None:
        """
        Attach the given handler to the root logger.
        """
        ft_logger = logging.getLogger("fontTools.ttLib.tables._p_o_s_t")
        ft_logger.setLevel(logging.ERROR)
        ft_logger.propagate = False

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        logger.handlers = [
            h for h in logger.handlers if not isinstance(h, RichLogHandler)
        ]
        logger.addHandler(handler)

    async def _update_progress(self, done: int, total: int) -> None:
        prog = self.query_one("#prog", ProgressBar)
        label = self.query_one("#label-progress", Static)

        prog.update(total=total, progress=min(done, total))

        label.update(f"下载进度: {done}/{total} 章")
