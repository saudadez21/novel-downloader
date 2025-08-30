#!/usr/bin/env python3
"""
novel_downloader.config.adapter
-------------------------------

Defines ConfigAdapter, which maps a raw configuration dictionary and
site name into structured dataclass-based config models.
"""

import json
from typing import Any, TypeVar, cast

from novel_downloader.models import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
    TextCleanerConfig,
)

T = TypeVar("T")


class ConfigAdapter:
    """
    Adapter to map a raw configuration dictionary and site name
    into structured dataclass configuration models.
    """

    def __init__(self, config: dict[str, Any], site: str):
        """
        Initialize the adapter.

        :param config: The fully loaded configuration dictionary.
        :param site: The current site name (e.g. "qidian").
        """
        self._config = config
        self._site = site
        self._site_cfg: dict[str, Any] = self._get_site_cfg()
        self._gen_cfg: dict[str, Any] = config.get("general") or {}

    def get_fetcher_config(self) -> FetcherConfig:
        """
        Build a FetcherConfig from the raw configuration.

        :return: A FetcherConfig instance with all fields populated.
        """
        return FetcherConfig(
            request_interval=self._get_gen_cfg("request_interval", 2.0),
            retry_times=self._get_gen_cfg("retry_times", 3),
            backoff_factor=self._get_gen_cfg("backoff_factor", 2.0),
            timeout=self._get_gen_cfg("timeout", 30.0),
            max_connections=self._get_gen_cfg("max_connections", 10),
            max_rps=self._get_gen_cfg("max_rps", 1000.0),
            user_agent=self._get_gen_cfg("user_agent", None),
            headers=self._get_gen_cfg("headers", None),
            verify_ssl=self._get_gen_cfg("verify_ssl", True),
            locale_style=self._get_gen_cfg("locale_style", "simplified"),
        )

    def get_downloader_config(self) -> DownloaderConfig:
        """
        Build a DownloaderConfig using both general and site-specific settings.

        :return: A DownloaderConfig instance with all fields populated.
        """
        gen = self._config.get("general", {})
        debug = gen.get("debug", {})
        return DownloaderConfig(
            request_interval=self._get_gen_cfg("request_interval", 2.0),
            retry_times=self._get_gen_cfg("retry_times", 3),
            backoff_factor=self._get_gen_cfg("backoff_factor", 2.0),
            workers=self._get_gen_cfg("workers", 2),
            skip_existing=self._get_gen_cfg("skip_existing", True),
            login_required=self._site_cfg.get("login_required", False),
            save_html=debug.get("save_html", False),
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            storage_batch_size=gen.get("storage_batch_size", 1),
        )

    def get_parser_config(self) -> ParserConfig:
        """
        Build a ParserConfig from general, OCR, and site-specific settings.

        :return: A ParserConfig instance with all fields populated.
        """
        gen = self._config.get("general", {})
        font_ocr = gen.get("font_ocr", {})
        return ParserConfig(
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            use_truncation=self._site_cfg.get("use_truncation", True),
            decode_font=font_ocr.get("decode_font", False),
            save_font_debug=font_ocr.get("save_font_debug", False),
            batch_size=font_ocr.get("batch_size", 32),
        )

    def get_exporter_config(self) -> ExporterConfig:
        """
        Build an ExporterConfig from output and general settings.

        :return: An ExporterConfig instance with all fields populated.
        """
        gen = self._config.get("general", {})
        out = self._config.get("output", {})
        cln = self._config.get("cleaner", {})
        fmt = out.get("formats", {})
        naming = out.get("naming", {})
        epub_opts = out.get("epub", {})
        cleaner_cfg = self._dict_to_cleaner_cfg(cln)
        return ExporterConfig(
            cache_dir=gen.get("cache_dir", "./novel_cache"),
            raw_data_dir=gen.get("raw_data_dir", "./raw_data"),
            output_dir=gen.get("output_dir", "./downloads"),
            clean_text=cln.get("clean_text", True),
            make_txt=fmt.get("make_txt", True),
            make_epub=fmt.get("make_epub", False),
            make_md=fmt.get("make_md", False),
            make_pdf=fmt.get("make_pdf", False),
            append_timestamp=naming.get("append_timestamp", True),
            filename_template=naming.get("filename_template", "{title}_{author}"),
            include_cover=epub_opts.get("include_cover", True),
            include_picture=epub_opts.get("include_picture", True),
            split_mode=self._site_cfg.get("split_mode", "book"),
            cleaner_cfg=cleaner_cfg,
        )

    def get_login_config(self) -> dict[str, str]:
        """
        Return the subset of login fields present in current site config:
            * `username`
            * `password`
            * `cookies`
        """
        out: dict[str, str] = {}
        for key in ("username", "password", "cookies"):
            val = self._site_cfg.get(key, "")
            val = val.strip()
            if val:
                out[key] = val
        return out

    def get_book_ids(self) -> list[BookConfig]:
        """
        Extract the list of target books from the site configuration.

        The site config may specify book_ids as:
          * a single string or integer
          * a dict with book_id and optional start_id, end_id, ignore_ids
          * a list of the above types

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

    def get_log_level(self) -> str:
        """
        Retrieve the logging level from [general.debug].

        :return: The configured log level ("DEBUG", "INFO", "WARNING", "ERROR").
        """
        debug_cfg = self._config.get("general", {}).get("debug", {})
        return debug_cfg.get("log_level") or "INFO"

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
        self._site_cfg = self._get_site_cfg()

    def _get_gen_cfg(self, key: str, default: T) -> T:
        return self._site_cfg.get(key) or self._gen_cfg.get(key) or default

    def _get_site_cfg(self) -> dict[str, Any]:
        """
        Retrieve the configuration for a specific site.

        Lookup order:
          1. If there is a site-specific entry under config["sites"], return that.
          2. Otherwise, if a "common" entry exists under config["sites"], return that.
          3. If neither is present, return an empty dict.

        :param site: Optional override of the site name; defaults to self._site.
        :return: The site-specific or common configuration dict.
        """
        sites_cfg = self._config.get("sites") or {}

        if self._site in sites_cfg:
            return sites_cfg[self._site] or {}

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
        if title_ext.get("enabled", False):
            title_ext_rm_p = title_ext.get("remove_patterns", "")
            title_ext_rp_p = title_ext.get("replace", "")

            title_remove_ext = cls._load_str_list(title_ext_rm_p)
            title_remove += title_remove_ext

            title_repl_ext = cls._load_str_dict(title_ext_rp_p)
            title_repl = {**title_repl, **title_repl_ext}

        # Content rules
        content_section = cfg.get("content", {})
        content_remove = content_section.get("remove_patterns", [])
        content_repl = content_section.get("replace", {})

        content_ext = content_section.get("external", {})

        if content_ext.get("enabled", False):
            content_ext_rm_p = content_ext.get("remove_patterns", "")
            content_ext_rp_p = content_ext.get("replace", "")

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
