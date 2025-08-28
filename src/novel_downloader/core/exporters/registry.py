#!/usr/bin/env python3
"""
novel_downloader.core.exporters.registry
----------------------------------------

Registry and factory helpers for creating site-specific or common exporters.
"""

__all__ = ["register_exporter", "get_exporter"]

from collections.abc import Callable, Sequence
from typing import TypeVar

from novel_downloader.core.exporters.common import CommonExporter
from novel_downloader.core.interfaces import ExporterProtocol
from novel_downloader.models import ExporterConfig

ExporterBuilder = Callable[[ExporterConfig], ExporterProtocol]

E = TypeVar("E", bound=ExporterProtocol)
_EXPORTER_MAP: dict[str, ExporterBuilder] = {}


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


def get_exporter(site: str, config: ExporterConfig) -> ExporterProtocol:
    """
    Returns a site-specific exporter instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the exporter
    :return: An instance of a exporter class
    """
    site_key = site.lower()
    try:
        exporter_cls = _EXPORTER_MAP[site_key]
    except KeyError:
        return CommonExporter(config, site_key)
    return exporter_cls(config)
