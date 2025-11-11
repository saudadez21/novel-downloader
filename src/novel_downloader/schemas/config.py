#!/usr/bin/env python3
"""
novel_downloader.schemas.config
-------------------------------

Defines structured configuration models using dataclasses for each
major component in the novel_downloader pipeline.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FetcherConfig:
    request_interval: float = 0.5
    retry_times: int = 3
    backoff_factor: float = 2.0
    timeout: float = 30.0
    max_connections: int = 10
    max_rps: float = 1000.0
    user_agent: str | None = None
    headers: dict[str, str] | None = None
    impersonate: str | None = None
    verify_ssl: bool = True
    http2: bool = True
    proxy: str | None = None
    proxy_user: str | None = None
    proxy_pass: str | None = None
    trust_env: bool = False
    cache_dir: str = "./novel_cache"
    backend: str = "aiohttp"
    locale_style: str = "simplified"


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
class ExporterConfig:
    append_timestamp: bool = True
    filename_template: str = "{title}_{author}"
    include_picture: bool = True
    split_mode: str = "book"


@dataclass
class ClientConfig:
    request_interval: float = 0.5
    retry_times: int = 3
    backoff_factor: float = 2.0
    cache_dir: str = "./novel_cache"
    raw_data_dir: str = "./raw_data"
    output_dir: str = "./downloads"
    workers: int = 4
    skip_existing: bool = True
    save_html: bool = False
    storage_batch_size: int = 1
    fetcher_cfg: FetcherConfig = field(default_factory=FetcherConfig)
    parser_cfg: ParserConfig = field(default_factory=ParserConfig)


@dataclass
class ProcessorConfig:
    name: str  # "cleaner" | "corrector" | ...
    overwrite: bool = False
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    raw_data_dir: str = "./raw_data"
    processors: list[ProcessorConfig] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class BookConfig:
    book_id: str
    start_id: str | None = None
    end_id: str | None = None
    ignore_ids: frozenset[str] = field(default_factory=frozenset)
