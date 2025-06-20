#!/usr/bin/env python3
"""
novel_downloader.config.adapter
-------------------------------

Defines ConfigAdapter, which maps a raw configuration dictionary and
site name into structured dataclass-based config models.
"""

from typing import Any

from novel_downloader.models import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
)
from novel_downloader.utils.constants import SUPPORTED_SITES

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

    def get_fetcher_config(self) -> FetcherConfig:
        """
        从 config["requests"] 中读取通用请求配置
        返回 FetcherConfig 实例
        """
        gen = self._config.get("general", {})
        req = self._config.get("requests", {})
        site_cfg = self._get_site_cfg()
        return FetcherConfig(
            request_interval=gen.get("request_interval", 2.0),
            retry_times=req.get("retry_times", 3),
            backoff_factor=req.get("backoff_factor", 2.0),
            timeout=req.get("timeout", 30.0),
            max_connections=req.get("max_connections", 10),
            max_rps=req.get("max_rps", None),
            headless=req.get("headless", False),
            disable_images=req.get("disable_images", False),
            mode=site_cfg.get("mode", "session"),
            proxy=req.get("proxy", None),
            user_agent=req.get("user_agent", None),
            headers=req.get("headers", None),
            browser_type=req.get("browser_type", "chromium"),
            verify_ssl=req.get("verify_ssl", True),
        )

    def get_downloader_config(self) -> DownloaderConfig:
        """
        从 config["general"] 和 config["sites"][site] 中读取下载器相关配置,
        返回 DownloaderConfig 实例
        """
        gen = self._config.get("general", {})
        req = self._config.get("requests", {})
        debug = gen.get("debug", {})
        site_cfg = self._get_site_cfg()
        return DownloaderConfig(
            request_interval=gen.get("request_interval", 2.0),
            retry_times=req.get("retry_times", 3),
            backoff_factor=req.get("backoff_factor", 2.0),
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            download_workers=gen.get("download_workers", 2),
            parser_workers=gen.get("parser_workers", 2),
            skip_existing=gen.get("skip_existing", True),
            login_required=site_cfg.get("login_required", False),
            save_html=debug.get("save_html", False),
            mode=site_cfg.get("mode", "session"),
            storage_backend=gen.get("storage_backend", "json"),
            storage_batch_size=gen.get("storage_batch_size", 1),
            username=site_cfg.get("username", ""),
            password=site_cfg.get("password", ""),
            cookies=site_cfg.get("cookies", ""),
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
            use_truncation=site_cfg.get("use_truncation", True),
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

    def get_exporter_config(self) -> ExporterConfig:
        """
        从 config["general"] 与 config["output"] 中读取存储器相关配置,
        返回 ExporterConfig 实例
        """
        gen = self._config.get("general", {})
        out = self._config.get("output", {})
        fmt = out.get("formats", {})
        naming = out.get("naming", {})
        epub_opts = out.get("epub", {})
        site_cfg = self._get_site_cfg()
        return ExporterConfig(
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
            split_mode=site_cfg.get("split_mode", "book"),
        )

    def get_book_ids(self) -> list[BookConfig]:
        """
        从 config["sites"][site]["book_ids"] 中提取目标书籍列表
        """
        site_cfg = self._get_site_cfg()
        raw = site_cfg.get("book_ids", [])

        if isinstance(raw, str | int):
            return [{"book_id": str(raw)}]

        if isinstance(raw, dict):
            return [self._dict_to_book_config(raw)]

        if not isinstance(raw, list):
            raise ValueError(
                f"book_ids must be a list or string, got {type(raw).__name__}"
            )

        result: list[BookConfig] = []
        for item in raw:
            try:
                if isinstance(item, str | int):
                    result.append({"book_id": str(item)})
                elif isinstance(item, dict):
                    result.append(self._dict_to_book_config(item))
            except ValueError:
                continue

        return result

    @staticmethod
    def _dict_to_book_config(data: dict[str, Any]) -> BookConfig:
        """
        Converts a dict to BookConfig with type normalization.
        Raises ValueError if 'book_id' is missing.
        """
        if "book_id" not in data:
            raise ValueError("Missing required field 'book_id'")

        result: BookConfig = {"book_id": str(data["book_id"])}

        if "start_id" in data:
            result["start_id"] = str(data["start_id"])

        if "end_id" in data:
            result["end_id"] = str(data["end_id"])

        if "ignore_ids" in data:
            result["ignore_ids"] = [str(x) for x in data["ignore_ids"]]

        return result
