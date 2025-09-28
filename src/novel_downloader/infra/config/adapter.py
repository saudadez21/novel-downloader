#!/usr/bin/env python3
"""
novel_downloader.infra.config.adapter
-------------------------------------

Defines ConfigAdapter, which maps a raw configuration dictionary and
site into structured dataclass-based config models.
"""

import contextlib
import json
from collections.abc import Mapping
from typing import Any, TypeVar

from novel_downloader.schemas import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    FontOCRConfig,
    ParserConfig,
    TextCleanerConfig,
)

T = TypeVar("T")


class ConfigAdapter:
    """
    Adapter to map a raw configuration dictionary and site name
    into structured dataclass configuration models.

    Resolution order for each field:
      1. ``config["sites"][<site>]`` (if present)
      2. ``config["general"]`` (if present)
      3. Hard-coded default passed by the caller
    """

    def __init__(self, config: Mapping[str, Any], site: str):
        """
        Initialize the adapter with a configuration mapping and a site key.

        :param config: Fully loaded configuration mapping.
        :param site: Current site key (e.g., ``"qidian"``).
        """
        self._config: dict[str, Any] = dict(config)
        self._site: str = site

    def get_fetcher_config(self) -> FetcherConfig:
        """
        Build a :class:`novel_downloader.models.FetcherConfig` by resolving fields
        from site-specific and general settings.

        :return: Fully populated configuration for the network fetcher.
        """
        s, g = self._site_cfg, self._gen_cfg
        return FetcherConfig(
            request_interval=self._pick("request_interval", 0.5, s, g),
            retry_times=self._pick("retry_times", 3, s, g),
            backoff_factor=self._pick("backoff_factor", 2.0, s, g),
            timeout=self._pick("timeout", 30.0, s, g),
            max_connections=self._pick("max_connections", 10, s, g),
            max_rps=self._pick("max_rps", 1000.0, s, g),
            user_agent=self._pick("user_agent", None, s, g),
            headers=self._pick("headers", None, s, g),
            verify_ssl=self._pick("verify_ssl", True, s, g),
            locale_style=self._pick("locale_style", "simplified", s, g),
        )

    def get_downloader_config(self) -> DownloaderConfig:
        """
        Build a :class:`novel_downloader.models.DownloaderConfig` using both
        general and site-specific settings.

        :return: Fully populated configuration for the chapter/page downloader.
        """
        s, g = self._site_cfg, self._gen_cfg
        debug = g.get("debug") or {}
        return DownloaderConfig(
            request_interval=self._pick("request_interval", 0.5, s, g),
            retry_times=self._pick("retry_times", 3, s, g),
            backoff_factor=self._pick("backoff_factor", 2.0, s, g),
            workers=self._pick("workers", 2, s, g),
            skip_existing=self._pick("skip_existing", True, s, g),
            login_required=bool(s.get("login_required", False)),
            save_html=bool(debug.get("save_html", False)),
            raw_data_dir=g.get("raw_data_dir", "./raw_data"),
            cache_dir=g.get("cache_dir", "./novel_cache"),
            storage_batch_size=g.get("storage_batch_size", 1),
        )

    def get_parser_config(self) -> ParserConfig:
        """
        Build a :class:`novel_downloader.models.ParserConfig` from general,
        OCR-related, and site-specific settings.

        :return: Fully populated configuration for the parser stage.
        """
        s, g = self._site_cfg, self._gen_cfg
        g_font = g.get("font_ocr") or {}
        s_font = s.get("font_ocr") or {}
        font_ocr: dict[str, Any] = {**g_font, **s_font}
        return ParserConfig(
            cache_dir=g.get("cache_dir", "./novel_cache"),
            use_truncation=bool(s.get("use_truncation", True)),
            decode_font=bool(font_ocr.get("decode_font", False)),
            save_font_debug=bool(font_ocr.get("save_font_debug", False)),
            batch_size=int(font_ocr.get("batch_size", 32)),
            fontocr_cfg=self._dict_to_fontocr_cfg(font_ocr),
        )

    def get_exporter_config(self) -> ExporterConfig:
        """
        Build an :class:`novel_downloader.models.ExporterConfig` from the
        ``output`` and ``cleaner`` sections plus general settings.

        :return: Fully populated configuration for text/ebook export.
        """
        s, g = self._site_cfg, self._gen_cfg
        out = self._config.get("output") or {}
        cln = self._config.get("cleaner") or {}
        fmt = out.get("formats") or {}
        naming = out.get("naming") or {}
        epub_opts = out.get("epub") or {}

        cleaner_cfg = self._dict_to_cleaner_cfg(cln)
        return ExporterConfig(
            cache_dir=g.get("cache_dir", "./novel_cache"),
            raw_data_dir=g.get("raw_data_dir", "./raw_data"),
            output_dir=g.get("output_dir", "./downloads"),
            check_missing=self._pick("check_missing", False, s, g),
            clean_text=cln.get("clean_text", False),
            make_txt=fmt.get("make_txt", True),
            make_epub=fmt.get("make_epub", True),
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
        Extract login-related fields from the current site configuration.
        Only non-empty string values are returned; values are stripped.

        :return: A subset of ``{"username","password","cookies"}`` that are non-empty
        """
        out: dict[str, str] = {}
        for key in ("username", "password", "cookies"):
            val = self._site_cfg.get(key, "")
            if isinstance(val, str):
                s = val.strip()
                if s:
                    out[key] = s
        return out

    def get_plugins_config(self) -> dict[str, Any]:
        """
        Return the plugin-related configuration section.
        """
        plugins_cfg = self._config.get("plugins") or {}
        return {
            "enable_local_plugins": plugins_cfg.get("enable_local_plugins", False),
            "local_plugins_path": plugins_cfg.get("local_plugins_path") or "",
        }

    def get_book_ids(self) -> list[BookConfig]:
        """
        Extract and normalize the list of target books for the current site.

        Accepted shapes for ``site.book_ids``:
          * a single ``str`` or ``int`` (book id)
          * a dict  with fields: book_id and optional start_id, end_id, ignore_ids
          * a ``list`` containing any mix of the above

        :return: Normalized list of :class:`BookConfig`-compatible dictionaries.
        :raises ValueError: If ``book_ids`` is neither a scalar ``str|int``, ``dict``,
                            nor ``list``.
        """
        raw = self._site_cfg.get("book_ids", [])

        if isinstance(raw, (str | int)):
            return [{"book_id": str(raw)}]

        if isinstance(raw, dict):
            return [self._dict_to_book_cfg(raw)]

        if not isinstance(raw, list):
            raise ValueError(
                f"book_ids must be a list or string, got {type(raw).__name__}"
            )

        result: list[BookConfig] = []
        for item in raw:
            if isinstance(item, (str | int)):
                result.append({"book_id": str(item)})
            elif isinstance(item, dict):
                result.append(self._dict_to_book_cfg(item))
            else:
                raise ValueError(
                    f"Invalid book_id entry: expected str|int|dict, got {type(item).__name__}"  # noqa: E501
                )
        return result

    def get_log_level(self) -> str:
        """
        Retrieve the logging level from ``general.debug``.

        :return: One of ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``
        """
        debug_cfg = self._gen_cfg.get("debug", {})
        return debug_cfg.get("log_level") or "INFO"

    @property
    def site(self) -> str:
        return self._site

    @site.setter
    def site(self, value: str) -> None:
        self._site = value

    @property
    def _gen_cfg(self) -> dict[str, Any]:
        """
        A read-only view of the global ``general`` settings.

        :return: ``config["general"]`` if present, else ``{}``.
        """
        return self._config.get("general") or {}

    @property
    def _site_cfg(self) -> dict[str, Any]:
        """
        Retrieve the configuration block for the current site.

        Lookup order:
          1. If a site-specific entry exists under ``config["sites"]``, return it.
          2. Otherwise, if ``config["sites"]["common"]`` exists, return it.
          3. Else return an empty dict.

        :return: Site-specific mapping, common mapping, or ``{}``.
        """
        sites_cfg = self._config.get("sites") or {}
        if self._site in sites_cfg and isinstance(sites_cfg[self._site], dict):
            return sites_cfg[self._site] or {}
        return sites_cfg.get("common") or {}

    @staticmethod
    def _has_key(d: Mapping[str, Any] | None, key: str) -> bool:
        """
        Check whether a mapping contains a key.

        :param d: Mapping to inspect.
        :param key: Key to look up.
        :return: ``True`` if ``d`` is a Mapping and contains key; otherwise ``False``.
        """
        return isinstance(d, Mapping) and (key in d)

    def _pick(self, key: str, default: T, *sources: Mapping[str, Any]) -> T:
        """
        Resolve ``key`` from the provided ``sources`` in order of precedence.

        :param key: Configuration key to resolve.
        :param default: Fallback value if ``key`` is absent in all sources.
        :param sources: One or more mappings to check, in order of precedence.
        :return: The first present value for ``key``, otherwise ``default``.
        """
        for src in sources:
            if self._has_key(src, key):
                return src[key]  # type: ignore[no-any-return]
        return default

    @staticmethod
    def _dict_to_book_cfg(data: dict[str, Any]) -> BookConfig:
        """
        Convert a raw dict into a :class:`novel_downloader.models.BookConfig`
        with normalized types (all IDs coerced to strings).

        :param data: A dict that must contain at least "book_id".
        :return: Normalized :class:`BookConfig` mapping.
        :raises ValueError: If ``"book_id"`` is missing.
        """
        if "book_id" not in data:
            raise ValueError("Missing required field 'book_id'")

        out: BookConfig = {"book_id": str(data["book_id"])}

        if "start_id" in data:
            out["start_id"] = str(data["start_id"])
        if "end_id" in data:
            out["end_id"] = str(data["end_id"])
        if "ignore_ids" in data:
            with contextlib.suppress(Exception):
                out["ignore_ids"] = [str(x) for x in data["ignore_ids"]]
        return out

    @staticmethod
    def _dict_to_fontocr_cfg(data: dict[str, Any]) -> FontOCRConfig:
        """
        Convert a raw ``font_ocr`` dict into a :class:`FontOCRConfig`.
        """
        if not isinstance(data, dict):
            return FontOCRConfig()

        ishape = data.get("input_shape")
        if isinstance(ishape, list):
            ishape = tuple(ishape)  # [C, H, W] -> (C, H, W)

        return FontOCRConfig(
            model_name=data.get("model_name"),
            model_dir=data.get("model_dir"),
            input_shape=ishape,
            device=data.get("device"),
            precision=data.get("precision", "fp32"),
            cpu_threads=data.get("cpu_threads", 10),
            enable_hpi=data.get("enable_hpi", False),
        )

    @classmethod
    def _dict_to_cleaner_cfg(cls, cfg: dict[str, Any]) -> TextCleanerConfig:
        """
        Convert a nested ``cleaner`` block into a
        :class:`novel_downloader.models.TextCleanerConfig`.

        :param cfg: configuration dictionary
        :return: Aggregated title/content rules with external file contents merged
        """
        t_remove, t_replace = cls._merge_rules(cfg.get("title", {}) or {})
        c_remove, c_replace = cls._merge_rules(cfg.get("content", {}) or {})
        return TextCleanerConfig(
            remove_invisible=cfg.get("remove_invisible", True),
            title_remove_patterns=t_remove,
            title_replacements=t_replace,
            content_remove_patterns=c_remove,
            content_replacements=c_replace,
        )

    @classmethod
    def _merge_rules(cls, section: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
        """
        Merge inline patterns/replacements with any enabled external files.

        :param section: Mapping describing either the ``title`` or ``content`` rules.
        :return: Tuple ``(remove_patterns, replace)`` after merging.
        """
        remove = list(section.get("remove_patterns") or [])
        replace = dict(section.get("replace") or {})
        ext = section.get("external") or {}
        if ext.get("enabled", False):
            rm_path = ext.get("remove_patterns") or ""
            rp_path = ext.get("replace") or ""
            remove += cls._load_str_list(rm_path)
            replace.update(cls._load_str_dict(rp_path))
        return remove, replace

    @staticmethod
    def _load_str_list(path: str) -> list[str]:
        """
        Load a JSON file containing a list of strings.

        :param path: File path to a JSON array (e.g., ``["a", "b"]``).
        :return: Parsed list on success; empty list if ``path`` is empty, file is
                 missing, or content is invalid.
        """
        if not path:
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return list(data) if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def _load_str_dict(path: str) -> dict[str, str]:
        """
        Load a JSON file containing a dict of string-to-string mappings.

        :param path: File path to a JSON object (e.g., ``{"old":"new"}``).
        :return: Parsed dict on success; empty dict if ``path`` is empty, file is
                 missing, or content is invalid.
        """
        if not path:
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                return dict(data) if isinstance(data, dict) else {}
        except Exception:
            return {}
