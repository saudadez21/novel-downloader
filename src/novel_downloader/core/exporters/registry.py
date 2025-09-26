#!/usr/bin/env python3
"""
novel_downloader.core.exporters.registry
----------------------------------------

Registry and factory helpers for creating site-specific or common exporters.
"""

__all__ = ["register_exporter", "get_exporter"]

from collections.abc import Callable, Sequence
from importlib import import_module
from typing import TypeVar

from novel_downloader.core.interfaces import ExporterProtocol
from novel_downloader.models import ExporterConfig

ExporterBuilder = Callable[[ExporterConfig, str], ExporterProtocol]

E = TypeVar("E", bound=ExporterProtocol)
_EXPORTER_MAP: dict[str, ExporterBuilder] = {}
_EXPORTERS_PKG = "novel_downloader.core.exporters"


def register_exporter(
    site_keys: Sequence[str],
) -> Callable[[type[E]], type[E]]:
    """
    Decorator to register a exporter class under given keys.

    :param site_keys: Sequence of site identifiers
    :return: A class decorator that populates _EXPORTER_MAP.
    """

    def decorator(cls: type[E]) -> type[E]:
        for key in site_keys:
            _EXPORTER_MAP[key.lower()] = cls
        return cls

    return decorator


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


def _load_exporter(site_key: str) -> None:
    """
    Attempt to import the site-specific exporter module.
    """
    modname = f"{_EXPORTERS_PKG}.{site_key}"
    try:
        import_module(modname)
    except ModuleNotFoundError as e:
        if e.name == modname:
            return
        raise


def get_exporter(site: str, config: ExporterConfig) -> ExporterProtocol:
    """
    Returns a site-specific exporter instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the exporter
    :return: An instance of a exporter class
    """
    site_key = _normalize_key(site)

    exporter_cls = _EXPORTER_MAP.get(site_key)
    if exporter_cls is None:
        _load_exporter(site_key)
        exporter_cls = _EXPORTER_MAP.get(site_key)

    if exporter_cls is None:
        from novel_downloader.core.exporters.common import CommonExporter

        return CommonExporter(config, site_key)

    return exporter_cls(config, site_key)
