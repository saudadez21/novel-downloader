#!/usr/bin/env python3
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

from typing import Any

from novel_downloader.utils.constants import SUPPORTED_SITES

from .models import (
    DownloaderConfig,
    ParserConfig,
    RequesterConfig,
    SaverConfig,
)
from .site_rules import load_site_rules


class ConfigAdapter:
    """
    Adapter to map a raw config dict + site name into structured dataclass configs.
    """

    def __init__(self, config: dict[str, Any], site: str):
        """
        :param config: 完整加载的配置 dict
        :param site:   当前站点名称 (e.g. "qidian")
        """
        self._config = config
        self._site = site

        site_rules = load_site_rules()  # -> Dict[str, SiteRules]
        self._supported_sites = set(site_rules.keys()) | SUPPORTED_SITES

    @property
    def site(self) -> str:
        return self._site

    @site.setter
    def site(self, value: str) -> None:
        self._site = value

    def _get_site_cfg(self, site: str | None = None) -> dict[str, Any]:
        """
        获取指定站点的配置 (默认为当前适配站点)

        1. 如果有 site-specific 配置, 优先返回它
        2. 否则, 如果该站点在支持站点中, 尝试返回 'common' 配置
        3. 否则返回空 dict
        """
        site = site or self._site
        sites_cfg = self._config.get("sites", {}) or {}

        if site in sites_cfg:
            return sites_cfg[site] or {}

        if site in self._supported_sites:
            return sites_cfg.get("common", {}) or {}

        return {}

    def get_requester_config(self) -> RequesterConfig:
        """
        从 config["requests"] 中读取通用请求配置 (含 DrissionPage 设置)
        返回 RequesterConfig 实例
        """
        req = self._config.get("requests", {})
        site_cfg = self._get_site_cfg()
        return RequesterConfig(
            retry_times=req.get("retry_times", 3),
            backoff_factor=req.get("backoff_factor", 2.0),
            timeout=req.get("timeout", 30.0),
            max_connections=req.get("max_connections", 10),
            max_rps=req.get("max_rps", None),
            headless=req.get("headless", True),
            user_data_folder=req.get("user_data_folder", "./user_data"),
            profile_name=req.get("profile_name", "Profile_1"),
            auto_close=req.get("auto_close", True),
            disable_images=req.get("disable_images", True),
            mute_audio=req.get("mute_audio", True),
            mode=site_cfg.get("mode", "session"),
            username=site_cfg.get("username", ""),
            password=site_cfg.get("password", ""),
        )

    def get_downloader_config(self) -> DownloaderConfig:
        """
        从 config["general"] 和 config["sites"][site] 中读取下载器相关配置,
        返回 DownloaderConfig 实例
        """
        gen = self._config.get("general", {})
        debug = gen.get("debug", {})
        site_cfg = self._get_site_cfg()
        return DownloaderConfig(
            request_interval=gen.get("request_interval", 5.0),
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            download_workers=gen.get("download_workers", 4),
            parser_workers=gen.get("parser_workers", 4),
            use_process_pool=gen.get("use_process_pool", True),
            skip_existing=gen.get("skip_existing", True),
            login_required=site_cfg.get("login_required", False),
            save_html=debug.get("save_html", False),
            mode=site_cfg.get("mode", "session"),
            storage_backend=gen.get("storage_backend", "json"),
            storage_batch_size=gen.get("storage_batch_size", 1),
        )

    def get_parser_config(self) -> ParserConfig:
        """
        从 config["general"]["cache_dir"]、config["general"]["debug"] 与
        config["sites"][site] 中读取解析器相关配置, 返回 ParserConfig 实例
        """
        gen = self._config.get("general", {})
        font_ocr = gen.get("font_ocr", {})
        site_cfg = self._get_site_cfg()
        return ParserConfig(
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            decode_font=font_ocr.get("decode_font", False),
            use_freq=font_ocr.get("use_freq", False),
            use_ocr=font_ocr.get("use_ocr", True),
            use_vec=font_ocr.get("use_vec", False),
            ocr_version=font_ocr.get("ocr_version", "v1.0"),
            save_font_debug=font_ocr.get("save_font_debug", False),
            batch_size=font_ocr.get("batch_size", 32),
            gpu_mem=font_ocr.get("gpu_mem", 500),
            gpu_id=font_ocr.get("gpu_id", None),
            ocr_weight=font_ocr.get("ocr_weight", 0.6),
            vec_weight=font_ocr.get("vec_weight", 0.4),
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
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            output_dir=gen.get("output_dir", "./downloads"),
            storage_backend=gen.get("storage_backend", "json"),
            clean_text=out.get("clean_text", True),
            make_txt=fmt.get("make_txt", True),
            make_epub=fmt.get("make_epub", False),
            make_md=fmt.get("make_md", False),
            make_pdf=fmt.get("make_pdf", False),
            append_timestamp=naming.get("append_timestamp", True),
            filename_template=naming.get("filename_template", "{title}_{author}"),
            include_cover=epub_opts.get("include_cover", True),
            include_toc=epub_opts.get("include_toc", False),
            include_picture=epub_opts.get("include_picture", False),
        )

    def get_book_ids(self) -> list[str]:
        """
        从 config["sites"][site]["book_ids"] 中提取目标书籍列表
        """
        site_cfg = self._get_site_cfg()
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
