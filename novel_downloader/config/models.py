#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.config.models
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


# === Requesters ===
@dataclass
class RequesterConfig:
    wait_time: int = 5
    retry_times: int = 3
    retry_interval: int = 5
    timeout: int = 30
    headless: bool = True
    user_data_folder: str = ""
    profile_name: str = ""
    auto_close: bool = True
    disable_images: bool = True
    mute_audio: bool = True
    mode: str = "session"  # browser / session


# === Downloaders ===
@dataclass
class DownloaderConfig:
    request_interval: int = 5
    raw_data_dir: str = "./raw_data"
    cache_dir: str = "./novel_cache"
    max_threads: int = 4
    skip_existing: bool = True
    login_required: bool = False
    save_html: bool = False


# === Parsers ===
@dataclass
class ParserConfig:
    cache_dir: str = "./novel_cache"
    decode_font: bool = False
    use_freq: bool = False
    use_ocr: bool = False
    save_font_debug: bool = False
    mode: str = "session"  # browser / session


# === Savers ===
@dataclass
class SaverConfig:
    raw_data_dir: str = "./raw_data"
    output_dir: str = "./downloads"
    clean_text: bool = True
    make_txt: bool = True
    make_epub: bool = False
    make_md: bool = False
    make_pdf: bool = False
    append_timestamp: bool = True
    filename_template: str = "{title}_{author}"
    include_cover: bool = True
    include_toc: bool = False
