#!/usr/bin/env python3
"""
novel_downloader.models.config
------------------------------

Defines structured configuration models using dataclasses for each
major component in the novel_downloader pipeline.

Each config section corresponds to a specific stage of the pipeline:
- RequesterConfig: network settings for requests and DrissionPage
- DownloaderConfig: chapter download behavior and local raw data paths
- ParserConfig: font decoding, cache handling, and debug options
- SaverConfig: output formatting, export formats, and filename templates

These models are used to map loaded YAML or JSON config data into
strongly typed Python objects for safer and cleaner access.
"""

from dataclasses import dataclass
from typing import NotRequired, TypedDict

from .types import (
    BrowserType,
    ModeType,
    SplitMode,
    StorageBackend,
)


@dataclass
class FetcherConfig:
    request_interval: float = 2.0
    retry_times: int = 3
    backoff_factor: float = 2.0
    timeout: float = 30.0
    headless: bool = False
    disable_images: bool = False
    mode: ModeType = "session"
    max_connections: int = 10
    max_rps: float | None = None  # Maximum requests per second
    proxy: str | None = None
    user_agent: str | None = None
    headers: dict[str, str] | None = None
    browser_type: BrowserType = "chromium"
    verify_ssl: bool = True


@dataclass
class DownloaderConfig:
    request_interval: float = 2.0
    retry_times: int = 3
    backoff_factor: float = 2.0
    raw_data_dir: str = "./raw_data"
    cache_dir: str = "./novel_cache"
    download_workers: int = 4
    parser_workers: int = 4
    skip_existing: bool = True
    login_required: bool = False
    save_html: bool = False
    mode: ModeType = "session"
    storage_backend: StorageBackend = "json"
    storage_batch_size: int = 1
    username: str = ""
    password: str = ""
    cookies: str = ""


@dataclass
class ParserConfig:
    cache_dir: str = "./novel_cache"
    use_truncation: bool = True
    decode_font: bool = False
    use_freq: bool = False
    use_ocr: bool = True
    use_vec: bool = False
    ocr_version: str = "v1.0"
    batch_size: int = 32
    gpu_mem: int = 500
    gpu_id: int | None = None
    ocr_weight: float = 0.6
    vec_weight: float = 0.4
    save_font_debug: bool = False
    mode: ModeType = "session"


@dataclass
class ExporterConfig:
    cache_dir: str = "./novel_cache"
    raw_data_dir: str = "./raw_data"
    output_dir: str = "./downloads"
    storage_backend: StorageBackend = "json"
    clean_text: bool = True
    make_txt: bool = True
    make_epub: bool = False
    make_md: bool = False
    make_pdf: bool = False
    append_timestamp: bool = True
    filename_template: str = "{title}_{author}"
    include_cover: bool = True
    include_toc: bool = False
    include_picture: bool = False
    split_mode: SplitMode = "book"


class BookConfig(TypedDict):
    book_id: str
    start_id: NotRequired[str]
    end_id: NotRequired[str]
    ignore_ids: NotRequired[list[str]]
