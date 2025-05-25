#!/usr/bin/env python3
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
from typing import Any, Literal, TypedDict

ModeType = Literal["browser", "session", "async"]
StorageBackend = Literal["json", "sqlite"]


# === Requesters ===
@dataclass
class RequesterConfig:
    retry_times: int = 3
    backoff_factor: float = 2.0
    timeout: float = 30.0
    headless: bool = True
    user_data_folder: str = ""
    profile_name: str = ""
    auto_close: bool = True
    disable_images: bool = True
    mute_audio: bool = True
    mode: ModeType = "session"
    max_connections: int = 10
    max_rps: float | None = None  # Maximum requests per second
    username: str = ""
    password: str = ""


# === Downloaders ===
@dataclass
class DownloaderConfig:
    request_interval: float = 5.0
    raw_data_dir: str = "./raw_data"
    cache_dir: str = "./novel_cache"
    download_workers: int = 4
    parser_workers: int = 4
    use_process_pool: bool = False
    skip_existing: bool = True
    login_required: bool = False
    save_html: bool = False
    mode: ModeType = "session"
    storage_backend: StorageBackend = "json"
    storage_batch_size: int = 1


# === Parsers ===
@dataclass
class ParserConfig:
    cache_dir: str = "./novel_cache"
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


# === Savers ===
@dataclass
class SaverConfig:
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


class RuleStep(TypedDict, total=False):
    # —— 操作类型 —— #
    type: Literal[
        "attr",
        "select_one",
        "select",
        "find",
        "find_all",
        "exclude",
        "regex",
        "text",
        "strip",
        "replace",
        "split",
        "join",
    ]

    # —— BeautifulSoup 相关 —— #
    selector: str | None  # CSS 选择器, 用于 select/select_one/exclude
    name: str | None  # 标签名称, 用于 find/find_all
    attrs: dict[str, Any] | None  # 属性过滤, 用于 find/find_all
    limit: int | None  # find_all 的最大匹配数
    attr: str | None  # 从元素获取属性值 (select/select_one/select_all)

    # —— 正则相关 —— #
    pattern: str | None  # 正则表达式
    flags: int | None  # re.I, re.M 等
    group: int | None  # 匹配结果中的第几个分组 (默认 0)
    template: str | None  # 自定义组合, 比如 "$1$2字"

    # —— 文本处理 —— #
    chars: str | None  # strip 要去除的字符集
    old: str | None  # replace 中要被替换的子串
    new: str | None  # replace 中新的子串
    count: int | None  # replace 中的最大替换次数
    sep: str | None  # split/join 的分隔符
    index: int | None  # split/select_all/select 之后取第几个元素


class FieldRules(TypedDict):
    steps: list[RuleStep]


class ChapterFieldRules(TypedDict):
    key: str
    steps: list[RuleStep]


class VolumesRulesOptional(TypedDict, total=False):
    volume_selector: str  # 有卷时选择 volume 块的 selector
    volume_name_steps: list[RuleStep]
    volume_mode: str  # Optional: "normal" (default) or "mixed"
    list_selector: str  # Optional: If "mixed" mode, parent container selector


class VolumesRules(VolumesRulesOptional):
    has_volume: bool  # 是否存在卷，false=未分卷
    chapter_selector: str  # 选择 chapter 节点的 selector
    chapter_steps: list[ChapterFieldRules]  # 提取章节信息的步骤列表


class BookInfoRules(TypedDict, total=False):
    book_name: FieldRules
    author: FieldRules
    cover_url: FieldRules
    update_time: FieldRules
    serial_status: FieldRules
    word_count: FieldRules
    summary: FieldRules
    volumes: VolumesRules


class ChapterRules(TypedDict, total=False):
    title: FieldRules
    content: FieldRules


class SiteProfile(TypedDict):
    book_info_url: str
    chapter_url: str


class SiteRules(TypedDict):
    profile: SiteProfile
    book_info: BookInfoRules
    chapter: ChapterRules


SiteRulesDict = dict[str, SiteRules]
