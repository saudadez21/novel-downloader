#!/usr/bin/env python3
"""
novel_downloader.core.factory.exporter
--------------------------------------

This module implements a factory function for creating exporter instances
based on the site name.
"""

from collections.abc import Callable

from novel_downloader.config import load_site_rules
from novel_downloader.core.exporters import (
    BiqugeExporter,
    CommonExporter,
    EsjzoneExporter,
    LinovelibExporter,
    QianbiExporter,
    QidianExporter,
    SfacgExporter,
    YamiboExporter,
)
from novel_downloader.core.interfaces import ExporterProtocol
from novel_downloader.models import ExporterConfig

ExporterBuilder = Callable[[ExporterConfig], ExporterProtocol]

_site_map: dict[str, ExporterBuilder] = {
    "biquge": BiqugeExporter,
    "esjzone": EsjzoneExporter,
    "linovelib": LinovelibExporter,
    "qianbi": QianbiExporter,
    "qidian": QidianExporter,
    "sfacg": SfacgExporter,
    "yamibo": YamiboExporter,
}


def get_exporter(site: str, config: ExporterConfig) -> ExporterProtocol:
    """
    Returns a site-specific exporter instance.

    :param site: Site name (e.g., 'qidian')
    :param config: Configuration for the exporter
    :return: An instance of a exporter class
    """
    site_key = site.lower()

    # site-specific
    if site_key in _site_map:
        return _site_map[site_key](config)

    # Fallback
    site_rules = load_site_rules()
    if site_key not in site_rules:
        raise ValueError(f"Unsupported site: {site}")

    return CommonExporter(config, site_key)
