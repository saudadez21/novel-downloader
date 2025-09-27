#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.linovelib.exporter
-------------------------------------------------

Exporter implementation for handling Linovelib novels.
"""

from pathlib import Path
from typing import Literal

from novel_downloader.infra.http_defaults import (
    DEFAULT_HEADERS,
    DEFAULT_IMAGE_SUFFIX,
)
from novel_downloader.plugins.common.exporter import CommonExporter
from novel_downloader.plugins.registry import registrar

_IMG_HEADERS = DEFAULT_HEADERS.copy()
_IMG_HEADERS["Referer"] = "https://www.linovelib.com/"


@registrar.register_exporter()
class LinovelibExporter(CommonExporter):
    """
    Exporter for 哔哩轻小说 novels.
    """

    @staticmethod
    def _download_image(
        img_url: str,
        target_dir: Path,
        filename: str | None = None,
        *,
        on_exist: Literal["overwrite", "skip", "rename"] = "overwrite",
    ) -> Path | None:
        """
        Download image from url to target dir with given name
        """
        from novel_downloader.infra.network import download

        return download(
            img_url,
            target_dir,
            filename=filename,
            headers=_IMG_HEADERS,
            on_exist=on_exist,
            default_suffix=DEFAULT_IMAGE_SUFFIX,
        )
