#!/usr/bin/env python3
"""
novel_downloader.schemas.config
-------------------------------

Defines structured configuration models using dataclasses for each
major component in the novel_downloader pipeline.
"""

from dataclasses import dataclass, field
from typing import NotRequired, TypedDict


@dataclass
class FetcherConfig:
    request_interval: float = 2.0
    retry_times: int = 3
    backoff_factor: float = 2.0
    timeout: float = 30.0
    max_connections: int = 10
    max_rps: float = 1000.0
    user_agent: str | None = None
    headers: dict[str, str] | None = None
    verify_ssl: bool = True
    locale_style: str = "simplified"


@dataclass
class DownloaderConfig:
    request_interval: float = 2.0
    retry_times: int = 3
    backoff_factor: float = 2.0
    raw_data_dir: str = "./raw_data"
    cache_dir: str = "./novel_cache"
    workers: int = 4
    skip_existing: bool = True
    login_required: bool = False
    save_html: bool = False
    storage_batch_size: int = 1


@dataclass
class FontOCRConfig:
    model_name: str | None = None
    model_dir: str | None = None
    input_shape: tuple[int, int, int] | None = None
    device: str | None = None
    precision: str = "fp32"
    cpu_threads: int = 10
    enable_hpi: bool = False


@dataclass
class ParserConfig:
    cache_dir: str = "./novel_cache"
    use_truncation: bool = True
    decode_font: bool = False
    batch_size: int = 32
    save_font_debug: bool = False
    fontocr_cfg: FontOCRConfig = field(default_factory=FontOCRConfig)


@dataclass
class TextCleanerConfig:
    remove_invisible: bool = True
    title_remove_patterns: list[str] = field(default_factory=list)
    title_replacements: dict[str, str] = field(default_factory=dict)
    content_remove_patterns: list[str] = field(default_factory=list)
    content_replacements: dict[str, str] = field(default_factory=dict)


@dataclass
class ExporterConfig:
    cache_dir: str = "./novel_cache"
    raw_data_dir: str = "./raw_data"
    output_dir: str = "./downloads"
    check_missing: bool = True
    clean_text: bool = True
    make_txt: bool = True
    make_epub: bool = False
    make_md: bool = False
    make_pdf: bool = False
    append_timestamp: bool = True
    filename_template: str = "{title}_{author}"
    include_cover: bool = True
    include_picture: bool = True
    split_mode: str = "book"
    cleaner_cfg: TextCleanerConfig = field(default_factory=TextCleanerConfig)


class BookConfig(TypedDict):
    book_id: str
    start_id: NotRequired[str]
    end_id: NotRequired[str]
    ignore_ids: NotRequired[list[str]]
