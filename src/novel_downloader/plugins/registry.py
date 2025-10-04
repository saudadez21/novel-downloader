#!/usr/bin/env python3
"""
novel_downloader.plugins.registry
---------------------------------
"""

from __future__ import annotations

import contextlib
import pkgutil
from importlib import import_module
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from novel_downloader.plugins.base.searcher import BaseSearcher
    from novel_downloader.plugins.protocols import (
        DownloaderProtocol,
        ExporterProtocol,
        FetcherProtocol,
        ParserProtocol,
        ProcessorProtocol,
    )
    from novel_downloader.schemas import (
        DownloaderConfig,
        ExporterConfig,
        FetcherConfig,
        ParserConfig,
    )

    DownloaderBuilder = Callable[
        [FetcherProtocol, ParserProtocol, DownloaderConfig, str],
        DownloaderProtocol,
    ]
    ExporterBuilder = Callable[[ExporterConfig, str], ExporterProtocol]
    FetcherBuilder = Callable[[FetcherConfig], FetcherProtocol]
    ParserBuilder = Callable[[ParserConfig], ParserProtocol]
    ProcessorBuilder = Callable[[dict[str, Any]], ProcessorProtocol]

    D = TypeVar("D", bound=DownloaderProtocol)
    E = TypeVar("E", bound=ExporterProtocol)
    F = TypeVar("F", bound=FetcherProtocol)
    P = TypeVar("P", bound=ParserProtocol)
    R = TypeVar("R", bound=ProcessorProtocol)  # Processor
    S = TypeVar("S", bound=type[BaseSearcher])

_PLUGINS_PKG = "novel_downloader.plugins"


class PluginRegistry:
    def __init__(self) -> None:
        self._downloaders: dict[str, DownloaderBuilder] = {}
        self._exporters: dict[str, ExporterBuilder] = {}
        self._fetchers: dict[str, FetcherBuilder] = {}
        self._parsers: dict[str, ParserBuilder] = {}
        self._processors: dict[str, ProcessorBuilder] = {}
        self._searchers: dict[str, type[BaseSearcher]] = {}
        self._sources: list[str] = [_PLUGINS_PKG]

    def register_fetcher(
        self, site_key: str | None = None
    ) -> Callable[[type[F]], type[F]]:
        def deco(cls: type[F]) -> type[F]:
            key = (site_key or cls.__module__.split(".")[-2]).lower()
            self._fetchers[key] = cls
            return cls

        return deco

    def register_parser(
        self, site_key: str | None = None
    ) -> Callable[[type[P]], type[P]]:
        def deco(cls: type[P]) -> type[P]:
            key = (site_key or cls.__module__.split(".")[-2]).lower()
            self._parsers[key] = cls
            return cls

        return deco

    def register_downloader(
        self, site_key: str | None = None
    ) -> Callable[[type[D]], type[D]]:
        def deco(cls: type[D]) -> type[D]:
            key = (site_key or cls.__module__.split(".")[-2]).lower()
            self._downloaders[key] = cls
            return cls

        return deco

    def register_exporter(
        self, site_key: str | None = None
    ) -> Callable[[type[E]], type[E]]:
        def deco(cls: type[E]) -> type[E]:
            key = (site_key or cls.__module__.split(".")[-2]).lower()
            self._exporters[key] = cls
            return cls

        return deco

    def register_processor(
        self, name: str | None = None
    ) -> Callable[[type[R]], type[R]]:
        def deco(cls: type[R]) -> type[R]:
            key = (name or self._derive_processor_key(cls.__module__)).lower()
            self._processors[key] = cls
            return cls

        return deco

    def register_searcher(self, site_key: str | None = None) -> Callable[[S], S]:
        def deco(cls: S) -> S:
            key = site_key or cls.__module__.split(".")[-2].lower()
            self._searchers[key] = cls
            return cls

        return deco

    def get_fetcher(self, site: str, config: FetcherConfig) -> FetcherProtocol:
        key = self._normalize_key(site)
        cls = self._fetchers.get(key)
        if cls is None:
            self._try_import_site(key, "fetcher")
            cls = self._fetchers.get(key)

        if cls is None:
            raise ValueError(f"Unsupported site: {site!r}")
        return cls(config)

    def get_parser(self, site: str, config: ParserConfig) -> ParserProtocol:
        key = self._normalize_key(site)
        cls = self._parsers.get(key)
        if cls is None:
            self._try_import_site(key, "parser")
            cls = self._parsers.get(key)

        if cls is None:
            raise ValueError(f"Unsupported site: {site!r}")
        return cls(config)

    def get_downloader(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        site: str,
        config: DownloaderConfig,
    ) -> DownloaderProtocol:
        key = self._normalize_key(site)
        cls = self._downloaders.get(key)
        if cls is None:
            self._try_import_site(key, "downloader")
            cls = self._downloaders.get(key)

        if cls is None:
            from novel_downloader.plugins.common.downloader import CommonDownloader

            return CommonDownloader(fetcher, parser, config, key)
        return cls(fetcher, parser, config, key)

    def get_exporter(self, site: str, config: ExporterConfig) -> ExporterProtocol:
        key = self._normalize_key(site)
        cls = self._exporters.get(key)
        if cls is None:
            self._try_import_site(key, "exporter")
            cls = self._exporters.get(key)

        if cls is None:
            from novel_downloader.plugins.common.exporter import CommonExporter

            return CommonExporter(config, key)
        return cls(config, key)

    def get_processor(self, name: str, config: dict[str, Any]) -> ProcessorProtocol:
        key = name.strip().lower()
        builder = self._processors.get(key)
        if builder is None:
            self._try_import_processor(key)
            builder = self._processors.get(key)
        if builder is None:
            raise ValueError(f"Unsupported processor: {name!r}")
        return builder(config)

    def get_searcher_class(self, site: str) -> type[BaseSearcher]:
        key = self._normalize_key(site)
        cls = self._searchers.get(key)
        if cls is None:
            self._try_import_site(key, "searcher")
            cls = self._searchers.get(key)
        if cls is None:
            raise ValueError(f"Unsupported site: {site!r}")
        return cls

    def get_searcher_classes(
        self,
        sites: Sequence[str] | None = None,
        *,
        load_all_if_none: bool = True,
    ) -> list[type[BaseSearcher]]:
        if sites:
            classes: list[type[BaseSearcher]] = []
            for site in sites:
                with contextlib.suppress(ValueError):
                    classes.append(self.get_searcher_class(site))
            return classes

        if load_all_if_none:
            self._load_all_sites("searcher")
        return list(self._searchers.values())

    @staticmethod
    def _normalize_key(site_key: str) -> str:
        """
        Normalize a site key to the expected module basename:
          * lowercase
          * if first char is a digit, prefix with 'n'
        """
        key = site_key.strip().lower()
        if not key:
            raise ValueError("Site key cannot be empty")
        if key[0].isdigit():
            return f"n{key}"
        return key

    @staticmethod
    def _derive_processor_key(modname: str) -> str:
        """
        Take module path after '.processors.' as key.
        Fallback to the last module segment if '.processors.' is not found.
        """
        if ".processors." in modname:
            return modname.split(".processors.", 1)[1]
        return modname.split(".")[-1]

    def _try_import_site(self, site_key: str, kind: str) -> None:
        """
        Attempt to import plugins for a given site/kind in order:
          1. built-in: `plugins.sites.<site>.<kind>`
          2. user-level: `<base>.sites.<site>.<kind>`
        """
        for base in self._sources:
            modname = f"{base}.sites.{site_key}.{kind}"
            try:
                import_module(modname)
                return
            except ModuleNotFoundError as e:
                if e.name and modname.startswith(e.name):
                    continue
                raise

    def _try_import_processor(self, key: str) -> None:
        """
        Attempt to import plugins for a given site/kind in order:
          1. built-in: `plugins.processors.<key>`
          2. user-level: `<base>.processors.<key>`
        """
        for base in self._sources:
            modname = f"{base}.processors.{key}"
            try:
                import_module(modname)
                return
            except ModuleNotFoundError as e:
                if e.name and modname.startswith(e.name):
                    continue
                raise

    def _load_all_sites(self, kind: str) -> None:
        """
        Scan all known plugin and import every `{namespace}.sites.<site>.<kind>`
        without failing if a site has no module for that kind.
        """
        for base in self._sources:
            try:
                pkg = import_module(f"{base}.sites")
            except ModuleNotFoundError:
                continue

            # iterate over site packages under *.sites
            for _, name, ispkg in pkgutil.iter_modules(
                pkg.__path__, pkg.__name__ + "."
            ):
                if not ispkg:
                    continue
                modname = f"{name}.{kind}"
                try:
                    import_module(modname)
                except ModuleNotFoundError as e:
                    if e.name and modname.startswith(e.name):
                        continue
                    raise

    def enable_local_plugins(
        self,
        local_plugins_path: str | None = None,
        override: bool = False,
    ) -> None:
        """
        Enable user-provided plugins under the `novel_plugins` namespace.

        Behavior:
          * If `local_plugins_path` is provided.
            * Add its parent dir to `sys.path`
            * Add its basename as a search base (namespace) to `self._sources`
          * If not provided, default to:
            * parent = os.getcwd()
            * namespace = "novel_plugins"
        """
        import os
        import sys

        if local_plugins_path:
            base = os.path.abspath(local_plugins_path)
            parent = os.path.dirname(base)
            namespace = os.path.basename(base)
        else:
            parent = os.getcwd()
            namespace = "novel_plugins"

        if parent not in sys.path:
            sys.path.append(parent)

        if namespace not in self._sources:
            if override:
                self._sources.insert(0, namespace)
            else:
                self._sources.append(namespace)


registrar = PluginRegistry()
