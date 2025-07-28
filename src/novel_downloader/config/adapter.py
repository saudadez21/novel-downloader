#!/usr/bin/env python3
"""
novel_downloader.config.adapter
-------------------------------

Defines ConfigAdapter, which maps a raw configuration dictionary and
site name into structured dataclass-based config models.
"""

import json
from typing import Any, cast

from novel_downloader.models import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    LogLevel,
    ParserConfig,
    TextCleanerConfig,
)


class ConfigAdapter:
    """
    Adapter to map a raw configuration dictionary and site name
    into structured dataclass configuration models.
    """

    _ALLOWED_LOG_LEVELS: tuple[LogLevel, ...] = (
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
    )

    def __init__(self, config: dict[str, Any], site: str):
        """
        Initialize the adapter.

        :param config: The fully loaded configuration dictionary.
        :param site:   The current site name (e.g. "qidian").
        """
        self._config = config
        self._site = site

    def get_fetcher_config(self) -> FetcherConfig:
        """
        Build a FetcherConfig from the raw configuration.

        Reads from:
          - config["general"] for global defaults (e.g. request_interval)
          - config["requests"] for HTTP-specific settings (timeouts, retries, etc.)
          - site-specific overrides under config["sites"][site]

        :return: A FetcherConfig instance with all fields populated.
        """
        gen = self._config.get("general", {})
        req = self._config.get("requests", {})
        return FetcherConfig(
            request_interval=gen.get("request_interval", 2.0),
            retry_times=req.get("retry_times", 3),
            backoff_factor=req.get("backoff_factor", 2.0),
            timeout=req.get("timeout", 30.0),
            max_connections=req.get("max_connections", 10),
            max_rps=req.get("max_rps", None),
            headless=req.get("headless", False),
            disable_images=req.get("disable_images", False),
            user_agent=req.get("user_agent", None),
            headers=req.get("headers", None),
            verify_ssl=req.get("verify_ssl", True),
            locale_style=gen.get("locale_style", "simplified"),
        )

    def get_downloader_config(self) -> DownloaderConfig:
        """
        Build a DownloaderConfig using both general and site-specific settings.

        Reads from:
          - config["general"] for download directories, worker counts, etc.
          - config["requests"] for retry and backoff settings
          - config["general"]["debug"] for debug toggles (e.g. save_html)
          - config["sites"][site] for login credentials and mode

        :return: A DownloaderConfig instance with all fields populated.
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
            workers=gen.get("workers", 2),
            skip_existing=gen.get("skip_existing", True),
            login_required=site_cfg.get("login_required", False),
            save_html=debug.get("save_html", False),
            storage_batch_size=gen.get("storage_batch_size", 1),
            username=site_cfg.get("username", ""),
            password=site_cfg.get("password", ""),
            cookies=site_cfg.get("cookies", ""),
        )

    def get_parser_config(self) -> ParserConfig:
        """
        Build a ParserConfig from general, OCR, and site-specific settings.

        Reads from:
          - config["general"]["cache_dir"] for where to cache intermediate parses
          - config["general"]["font_ocr"] for font-decoding and OCR options
          - config["sites"][site] for parsing mode and truncation behavior

        :return: A ParserConfig instance with all fields populated.
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
        )

    def get_exporter_config(self) -> ExporterConfig:
        """
        Build an ExporterConfig from output and general settings.

        Reads from:
          - config["general"] for cache and raw data directories
          - config["output"]["formats"] for which formats to generate
          - config["output"]["naming"] for filename templates
          - config["output"]["epub"] for EPUB-specific options
          - config["sites"][site] for export split mode

        :return: An ExporterConfig instance with all fields populated.
        """
        gen = self._config.get("general", {})
        out = self._config.get("output", {})
        cln = self._config.get("cleaner", {})
        fmt = out.get("formats", {})
        naming = out.get("naming", {})
        epub_opts = out.get("epub", {})
        site_cfg = self._get_site_cfg()
        cleaner_cfg = self._dict_to_cleaner_cfg(cln)
        return ExporterConfig(
            cache_dir=gen.get("cache_dir", "./novel_cache"),
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
            include_picture=epub_opts.get("include_picture", False),
            split_mode=site_cfg.get("split_mode", "book"),
            cleaner_cfg=cleaner_cfg,
        )

    def get_book_ids(self) -> list[BookConfig]:
        """
        Extract the list of target books from the site configuration.

        The site config may specify book_ids as:
          - a single string or integer
          - a dict with book_id and optional start_id, end_id, ignore_ids
          - a list of the above types

        :return: A list of BookConfig dicts.
        :raises ValueError: if the raw book_ids is neither a str/int, dict, nor list.
        """
        site_cfg = self._get_site_cfg()
        raw = site_cfg.get("book_ids", [])

        if isinstance(raw, str | int):
            return [{"book_id": str(raw)}]

        if isinstance(raw, dict):
            return [self._dict_to_book_cfg(raw)]

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
                    result.append(self._dict_to_book_cfg(item))
            except ValueError:
                continue

        return result

    def get_log_level(self) -> LogLevel:
        """
        Retrieve the logging level from [general.debug].

        Reads from config["general"]["debug"]["log_level"], defaulting to "INFO"
        if not set or invalid.

        :return: The configured LogLevel literal ("DEBUG", "INFO", "WARNING", "ERROR").
        """
        debug_cfg = self._config.get("general", {}).get("debug", {})
        raw = debug_cfg.get("log_level") or "INFO"
        if raw in self._ALLOWED_LOG_LEVELS:
            return cast(LogLevel, raw)
        return "INFO"

    @property
    def site(self) -> str:
        """
        Get the current site name.
        """
        return self._site

    @site.setter
    def site(self, value: str) -> None:
        """
        Set a new site name for configuration lookups.

        :param value: The new site key in config["sites"] to use.
        """
        self._site = value

    def _get_site_cfg(self, site: str | None = None) -> dict[str, Any]:
        """
        Retrieve the configuration for a specific site.

        Lookup order:
          1. If there is a site-specific entry under config["sites"], return that.
          2. Otherwise, if a "common" entry exists under config["sites"], return that.
          3. If neither is present, return an empty dict.

        :param site: Optional override of the site name; defaults to self._site.
        :return: The site-specific or common configuration dict.
        """
        site = site or self._site
        sites_cfg = self._config.get("sites") or {}

        if site in sites_cfg:
            return sites_cfg[site] or {}

        return sites_cfg.get("common") or {}

    @staticmethod
    def _dict_to_book_cfg(data: dict[str, Any]) -> BookConfig:
        """
        Convert a dictionary to a BookConfig with normalized types.

        :param data: A dict that must contain at least "book_id".
        :return: A BookConfig dict with all values cast to strings or lists of strings.
        :raises ValueError: if the "book_id" field is missing.
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

    @classmethod
    def _dict_to_cleaner_cfg(cls, cfg: dict[str, Any]) -> TextCleanerConfig:
        """
        Convert a nested dict of title/content rules into a TextCleanerConfig.

        :param cfg: configuration dictionary
        :return: fully constructed TextCleanerConfig
        """
        # Title rules
        title_section = cfg.get("title", {})
        title_remove = title_section.get("remove_patterns", [])
        title_repl = title_section.get("replace", {})

        title_ext = title_section.get("external", {})
        title_ext_en = title_ext.get("enabled", False)
        title_ext_rm_p = title_ext.get("remove_patterns", "")
        title_ext_rp_p = title_ext.get("replace", "")
        if title_ext_en:
            title_remove_ext = cls._load_str_list(title_ext_rm_p)
            title_remove += title_remove_ext

            title_repl_ext = cls._load_str_dict(title_ext_rp_p)
            title_repl = {**title_repl, **title_repl_ext}

        # Content rules
        content_section = cfg.get("content", {})
        content_remove = content_section.get("remove_patterns", [])
        content_repl = content_section.get("replace", {})

        content_ext = content_section.get("external", {})
        content_ext_en = content_ext.get("enabled", False)
        content_ext_rm_p = content_ext.get("remove_patterns", "")
        content_ext_rp_p = content_ext.get("replace", "")

        if content_ext_en:
            content_remove_ext = cls._load_str_list(content_ext_rm_p)
            content_remove += content_remove_ext

            content_repl_ext = cls._load_str_dict(content_ext_rp_p)
            content_repl = {**content_repl, **content_repl_ext}

        return TextCleanerConfig(
            remove_invisible=cfg.get("remove_invisible", True),
            title_remove_patterns=title_remove,
            title_replacements=title_repl,
            content_remove_patterns=content_remove,
            content_replacements=content_repl,
        )

    @staticmethod
    def _load_str_list(path: str) -> list[str]:
        try:
            with open(path, encoding="utf-8") as f:
                parsed = json.load(f)
            return cast(list[str], parsed)
        except Exception:
            return []

    @staticmethod
    def _load_str_dict(path: str) -> dict[str, str]:
        try:
            with open(path, encoding="utf-8") as f:
                parsed = json.load(f)
            return cast(dict[str, str], parsed)
        except Exception:
            return {}
