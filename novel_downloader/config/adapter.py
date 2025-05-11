#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.config.adapter
-------------------------------

Defines ConfigAdapter, which maps a raw configuration dictionary and
site name into structured dataclass-based config models.

Supported mappings:
- requests          -> RequesterConfig
- general+site      -> DownloaderConfig
- general+site      -> ParserConfig
- general+output    -> SaverConfig
- sites[site]       -> book_ids list
"""

from typing import Any, Dict, List

from .models import (
    DownloaderConfig,
    ParserConfig,
    RequesterConfig,
    SaverConfig,
)


class ConfigAdapter:
    """
    Adapter to map a raw config dict + site name into structured dataclass configs.
    """

    def __init__(self, config: Dict[str, Any], site: str):
        """
        :param config: 完整加载的配置 dict
        :param site:   当前站点名称 (e.g. "qidian")
        """
        self._config = config
        self._site = site

    def set_site(self, site: str) -> None:
        """
        切换当前适配的站点
        """
        self._site = site

    def get_requester_config(self) -> RequesterConfig:
        """
        从 config["requests"] 中读取通用请求配置 (含 DrissionPage 设置)
        返回 RequesterConfig 实例
        """
        req = self._config.get("requests", {})
        site_cfg = self._config.get("sites", {}).get(self._site, {})
        return RequesterConfig(
            wait_time=req.get("wait_time", 5),
            retry_times=req.get("retry_times", 3),
            retry_interval=req.get("retry_interval", 5),
            timeout=req.get("timeout", 30),
            headless=req.get("headless", True),
            user_data_folder=req.get("user_data_folder", "./user_data"),
            profile_name=req.get("profile_name", "Profile_1"),
            auto_close=req.get("auto_close", True),
            disable_images=req.get("disable_images", True),
            mute_audio=req.get("mute_audio", True),
            mode=site_cfg.get("mode", "session"),
        )

    def get_downloader_config(self) -> DownloaderConfig:
        """
        从 config["general"] 和 config["sites"][site] 中读取下载器相关配置,
        返回 DownloaderConfig 实例
        """
        gen = self._config.get("general", {})
        debug = gen.get("debug", {})
        site_cfg = self._config.get("sites", {}).get(self._site, {})
        return DownloaderConfig(
            request_interval=gen.get("request_interval", 5),
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            cache_dir=gen.get("cache_dir", "./cache"),
            max_threads=gen.get("max_threads", 4),
            skip_existing=gen.get("skip_existing", True),
            login_required=site_cfg.get("login_required", False),
            save_html=debug.get("save_html", False),
            mode=site_cfg.get("mode", "session"),
        )

    def get_parser_config(self) -> ParserConfig:
        """
        从 config["general"]["cache_dir"]、config["general"]["debug"] 与
        config["sites"][site] 中读取解析器相关配置, 返回 ParserConfig 实例
        """
        gen = self._config.get("general", {})
        site_cfg = self._config.get("sites", {}).get(self._site, {})
        return ParserConfig(
            cache_dir=gen.get("cache_dir", "./cache"),
            decode_font=site_cfg.get("decode_font", False),
            use_freq=site_cfg.get("use_freq", False),
            use_ocr=site_cfg.get("use_ocr", True),
            use_vec=site_cfg.get("use_vec", False),
            ocr_version=site_cfg.get("ocr_version", "v1.0"),
            save_font_debug=site_cfg.get("save_font_debug", False),
            batch_size=site_cfg.get("batch_size", 32),
            ocr_weight=site_cfg.get("ocr_weight", 0.6),
            vec_weight=site_cfg.get("vec_weight", 0.4),
            mode=site_cfg.get("mode", "session"),
        )

    def get_saver_config(self) -> SaverConfig:
        """
        从 config["general"] 与 config["output"] 中读取存储器相关配置,
        返回 SaverConfig 实例
        """
        gen = self._config.get("general", {})
        out = self._config.get("output", {})
        fmt = out.get("formats", {})
        naming = out.get("naming", {})
        epub_opts = out.get("epub", {})
        return SaverConfig(
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            output_dir=gen.get("output_dir", "./downloads"),
            clean_text=out.get("clean_text", True),
            make_txt=fmt.get("make_txt", True),
            make_epub=fmt.get("make_epub", False),
            make_md=fmt.get("make_md", False),
            make_pdf=fmt.get("make_pdf", False),
            append_timestamp=naming.get("append_timestamp", True),
            filename_template=naming.get("filename_template", "{title}_{author}"),
            include_cover=epub_opts.get("include_cover", True),
            include_toc=epub_opts.get("include_toc", False),
        )

    def get_book_ids(self) -> List[str]:
        """
        从 config["sites"][site]["book_ids"] 中提取目标书籍列表
        """
        site_cfg = self._config.get("sites", {}).get(self._site, {})
        raw_ids = site_cfg.get("book_ids", [])

        if isinstance(raw_ids, str):
            return [raw_ids]

        if isinstance(raw_ids, int):
            return [str(raw_ids)]

        if not isinstance(raw_ids, list):
            raise ValueError(
                f"book_ids must be a list or string, got {type(raw_ids).__name__}"
            )

        return [str(book_id) for book_id in raw_ids]
