#!/usr/bin/env python3
"""
novel_downloader.infra.config.adapter
-------------------------------------
"""

from pathlib import Path
from typing import Any

from novel_downloader.schemas import (
    BookConfig,
    ClientConfig,
    ExporterConfig,
    FetcherConfig,
    OCRConfig,
    ParserConfig,
    ProcessorConfig,
)


class ConfigAdapter:
    """Adapter that provides convenient access to general and site-specific settings."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the adapter.

        Args:
            config: A fully loaded configuration mapping.
        """
        self._config: dict[str, Any] = dict(config)

    def get_config(self) -> dict[str, Any]:
        """Return the entire configuration mapping.

        Returns:
            The raw configuration dictionary stored in this adapter.
        """
        return self._config

    def get_fetcher_config(self, site: str) -> FetcherConfig:
        """Build a FetcherConfig by resolving fields from site and general settings.

        Site-level settings override general ones; defaults are applied last.

        Args:
            site: The site key.

        Returns:
            A fully populated configuration for the network fetcher.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()
        cfg = {**general_cfg, **site_cfg}

        return FetcherConfig(
            cache_dir=general_cfg.get("cache_dir", "./novel_cache"),
            request_interval=cfg.get("request_interval", 0.5),
            retry_times=cfg.get("retry_times", 3),
            backoff_factor=cfg.get("backoff_factor", 2.0),
            timeout=cfg.get("timeout", 10.0),
            max_connections=cfg.get("max_connections", 10),
            max_rps=cfg.get("max_rps", 1000.0),
            user_agent=cfg.get("user_agent"),
            headers=cfg.get("headers"),
            impersonate=cfg.get("impersonate"),
            verify_ssl=cfg.get("verify_ssl", True),
            http2=cfg.get("http2", True),
            proxy=cfg.get("proxy"),
            proxy_user=cfg.get("proxy_user"),
            proxy_pass=cfg.get("proxy_pass"),
            trust_env=cfg.get("trust_env", False),
            backend=cfg.get("backend", "aiohttp"),
            locale_style=cfg.get("locale_style", "simplified"),
        )

    def get_parser_config(self, site: str) -> ParserConfig:
        """Build a ParserConfig from general, OCR-related, and site-specific settings.

        Args:
            site: The site key.

        Returns:
            A fully populated configuration for the parser stage.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()
        general_parser = general_cfg.get("parser") or {}
        site_parser = site_cfg.get("parser") or {}
        parser_cfg: dict[str, Any] = {**general_parser, **site_parser}

        return ParserConfig(
            cache_dir=general_cfg.get("cache_dir", "./novel_cache"),
            use_truncation=bool(parser_cfg.get("use_truncation", True)),
            enable_ocr=bool(parser_cfg.get("enable_ocr", False)),
            batch_size=int(parser_cfg.get("batch_size", 32)),
            remove_watermark=bool(parser_cfg.get("remove_watermark", False)),
            cut_mode=str(parser_cfg.get("cut_mode", "none")),
            ocr_cfg=self._dict_to_ocr_cfg(parser_cfg),
        )

    def get_client_config(self, site: str) -> ClientConfig:
        """Build a ClientConfig using both general and site-specific settings.

        Site-level settings override general ones; defaults are applied last.

        Args:
            site: The site key.

        Returns:
            A fully populated configuration for the high-level client.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()
        cfg = {**general_cfg, **site_cfg}
        debug_cfg = general_cfg.get("debug") or {}

        return ClientConfig(
            raw_data_dir=general_cfg.get("raw_data_dir", "./raw_data"),
            cache_dir=general_cfg.get("cache_dir", "./novel_cache"),
            output_dir=general_cfg.get("output_dir", "./downloads"),
            workers=cfg.get("workers", 4),
            request_interval=cfg.get("request_interval", 0.5),
            retry_times=cfg.get("retry_times", 3),
            backoff_factor=cfg.get("backoff_factor", 2.0),
            storage_batch_size=cfg.get("storage_batch_size", 1),
            cache_book_info=bool(cfg.get("cache_book_info", True)),
            cache_chapter=cfg.get("cache_chapter", True),
            fetch_inaccessible=cfg.get("fetch_inaccessible", False),
            save_html=bool(debug_cfg.get("save_html", False)),
            fetcher_cfg=self.get_fetcher_config(site),
            parser_cfg=self.get_parser_config(site),
        )

    def get_exporter_config(self, site: str) -> ExporterConfig:
        """Build an ExporterConfig from general.output with site-specific overrides.

        Args:
            site: The site key.

        Returns:
            The resolved exporter configuration.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()
        general_output = general_cfg.get("output") or {}
        site_output = site_cfg.get("output") or {}
        out = {**general_output, **site_output}

        return ExporterConfig(
            render_missing_chapter=out.get("render_missing_chapter", True),
            append_timestamp=out.get("append_timestamp", True),
            filename_template=out.get("filename_template", "{title}_{author}"),
            include_picture=out.get("include_picture", True),
            split_mode=out.get("split_mode", "book"),
        )

    def get_login_config(self, site: str) -> dict[str, str]:
        """Extract login-related fields from the current site configuration.

        Only non-empty string values are returned; values are stripped.

        Args:
            site: The site key.

        Returns:
            A subset of {"username", "password", "cookies"} that are non-empty.
        """
        site_cfg = self._site_cfg(site)
        out: dict[str, str] = {}
        for key in ("username", "password", "cookies"):
            val = site_cfg.get(key, "")
            if isinstance(val, str):
                s = val.strip()
                if s:
                    out[key] = s
        return out

    def get_login_required(self, site: str) -> bool:
        """Determine whether the given site requires login.

        Args:
            site: The site key.

        Returns:
            True if the site or general settings define ``login_required``.
            Defaults to False if unspecified.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()
        cfg = {**general_cfg, **site_cfg}
        return bool(cfg.get("login_required", False))

    def get_export_fmt(self, site: str) -> list[str]:
        """Return the list of export formats for a given site.

        Args:
            site: The site key.

        Returns:
            A list of enabled export format names. Empty if not configured.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()
        general_output = general_cfg.get("output") or {}
        site_output = site_cfg.get("output") or {}
        out = {**general_output, **site_output}
        fmt = out.get("formats")
        return fmt if isinstance(fmt, list) else []

    def get_plugins_config(self) -> dict[str, Any]:
        """Return the plugin-related configuration section.

        Returns:
            A mapping with normalized plugin-related configuration.
        """
        plugins_cfg = self._config.get("plugins") or {}
        return {
            "enable_local_plugins": plugins_cfg.get("enable_local_plugins", False),
            "local_plugins_path": plugins_cfg.get("local_plugins_path") or "",
            "override_builtins": plugins_cfg.get("override_builtins", False),
        }

    def get_processor_configs(self, site: str) -> list[ProcessorConfig]:
        """Build the list of ProcessorConfig objects for the given site.

        Site-specific processors take precedence over general ones. If the
        site defines any processors, only those are returned. Otherwise, the
        general processor list is used.

        Args:
            site: The site key.

        Returns:
            A list of ProcessorConfig objects in the order they should be run.
        """
        site_cfg, general_cfg = self._site_cfg(site), self._gen_cfg()

        site_rows = site_cfg.get("processors") or []
        site_procs = self._to_processor_cfgs(site_rows)
        general_rows = general_cfg.get("processors") or []
        general_procs = self._to_processor_cfgs(general_rows)

        return site_procs if site_procs else general_procs

    def get_book_ids(self, site: str) -> list[BookConfig]:
        """Extract and normalize the list of target books for the current site.

        Accepted shapes for ``site.book_ids``:
          * a single str or int (book id)
          * a dict with fields: ``book_id`` and optional ``start_id``, ``end_id``,
            ``ignore_ids``
          * a list containing any mix of the above

        Args:
            site: The site key.

        Returns:
            A normalized list of BookConfig objects.

        Raises:
            ValueError: If ``book_ids`` is neither a scalar ``str|int``, dict, list.
        """
        site_cfg = self._site_cfg(site)
        raw = site_cfg.get("book_ids", [])

        if isinstance(raw, (str, int)):
            return [self._dict_to_book_cfg({"book_id": raw})]

        if isinstance(raw, dict):
            return [self._dict_to_book_cfg(raw)]

        if not isinstance(raw, list):
            raise ValueError(
                f"book_ids must be a list or string, got {type(raw).__name__}"
            )

        result: list[BookConfig] = []
        for item in raw:
            if isinstance(item, (str, int)):
                result.append(self._dict_to_book_cfg({"book_id": item}))
            elif isinstance(item, dict):
                result.append(self._dict_to_book_cfg(item))
            else:
                raise ValueError(
                    f"Invalid book_id entry: expected str|int|dict, got {type(item).__name__}"  # noqa: E501
                )
        return result

    def get_log_level(self) -> str:
        """Return the configured logging level.

        The value is taken from ``general.debug.log_level``. If missing,
        ``"INFO"`` is returned.

        Returns:
            The logging level string.
        """
        debug_cfg = self._gen_cfg().get("debug", {})
        return debug_cfg.get("log_level") or "INFO"

    def get_log_dir(self) -> Path:
        """Return the directory used to store log files.

        This reads ``general.debug.log_dir``. Defaults to ``"./logs"``.

        Returns:
            An absolute Path to the log directory.
        """
        debug_cfg = self._gen_cfg().get("debug", {})
        log_dir = debug_cfg.get("log_dir") or "./logs"
        return Path(log_dir).expanduser().resolve()

    def get_cache_dir(self) -> Path:
        """Return the directory used for local resource caching.

        This corresponds to ``general.cache_dir``. Defaults to
        ``"./novel_cache"``.

        Returns:
            An absolute Path to the cache directory.
        """
        cache_dir = self._gen_cfg().get("cache_dir") or "./novel_cache"
        return Path(cache_dir).expanduser().resolve()

    def get_raw_data_dir(self) -> Path:
        """Return the directory used to store raw scraped data.

        This corresponds to ``general.raw_data_dir``. Defaults to
        ``"./raw_data"``.

        Returns:
            An absolute Path for storing raw scraped data.
        """
        raw_data_dir = self._gen_cfg().get("raw_data_dir") or "./raw_data"
        return Path(raw_data_dir).expanduser().resolve()

    def get_output_dir(self) -> Path:
        """Return the directory used for final output files.

        This corresponds to ``general.output_dir``. Defaults to
        ``"./downloads"``.

        Returns:
            An absolute Path to the output directory.
        """
        output_dir = self._gen_cfg().get("output_dir") or "./downloads"
        return Path(output_dir).expanduser().resolve()

    def _gen_cfg(self) -> dict[str, Any]:
        """Return the global ``general`` configuration mapping.

        Returns:
            The ``general`` dictionary or an empty dict if missing or invalid.
        """
        general = self._config.get("general")
        return general if isinstance(general, dict) else {}

    def _site_cfg(self, site: str) -> dict[str, Any]:
        """Return the configuration block for the given site.

        Args:
            site: The site name.

        Returns:
            A dictionary representing the site's configuration, or an empty
            dict if missing or invalid.
        """
        sites_cfg = self._config.get("sites") or {}
        value = sites_cfg.get(site)
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _dict_to_book_cfg(data: dict[str, Any]) -> BookConfig:
        """Convert a raw dict into a BookConfig with normalized types.

        All IDs are coerced to strings.

        Args:
            data: A mapping that must contain at least ``"book_id"``.

        Returns:
            A normalized BookConfig instance.

        Raises:
            ValueError: If ``"book_id"`` is missing.
        """
        if "book_id" not in data:
            raise ValueError("Missing required field 'book_id'")

        book_id = str(data["book_id"])
        start_id = str(data["start_id"]) if "start_id" in data else None
        end_id = str(data["end_id"]) if "end_id" in data else None

        ignore_ids: frozenset[str] = frozenset()
        if "ignore_ids" in data:
            ignore_ids = frozenset(str(x) for x in data["ignore_ids"])

        return BookConfig(
            book_id=book_id,
            start_id=start_id,
            end_id=end_id,
            ignore_ids=ignore_ids,
        )

    @staticmethod
    def _dict_to_ocr_cfg(data: dict[str, Any]) -> OCRConfig:
        """Convert a raw font_ocr dict into an OCRConfig.

        Args:
            data: The raw OCR configuration mapping.

        Returns:
            An OCRConfig instance with normalized values.
        """
        if not isinstance(data, dict):
            return OCRConfig()

        ishape = data.get("input_shape")
        if isinstance(ishape, list):
            # [C, H, W] -> (C, H, W)
            ishape = tuple(ishape)

        return OCRConfig(
            model_name=data.get("model_name"),
            model_dir=data.get("model_dir"),
            input_shape=ishape,
            device=data.get("device"),
            precision=data.get("precision", "fp32"),
            cpu_threads=data.get("cpu_threads", 10),
            enable_hpi=data.get("enable_hpi", False),
        )

    @staticmethod
    def _to_processor_cfgs(data: list[dict[str, Any]]) -> list[ProcessorConfig]:
        """Convert a list of raw processor table dicts into ProcessorConfig objects.

        Args:
            data: A list of raw processor configuration mappings.

        Returns:
            A list of ProcessorConfig objects.
        """
        if not isinstance(data, list):
            return []

        result: list[ProcessorConfig] = []
        for row in data:
            if not isinstance(row, dict):
                continue

            name = str(row.get("name", "")).strip().lower()
            if not name:
                continue

            overwrite = bool(row.get("overwrite", False))
            # Pass everything else as options.
            opts = {k: v for k, v in row.items() if k not in ("name", "overwrite")}
            result.append(ProcessorConfig(name=name, overwrite=overwrite, options=opts))

        return result
