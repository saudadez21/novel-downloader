#!/usr/bin/env python3
"""
novel_downloader.models.site_rules
----------------------------------

"""

from typing import Any, Literal, TypedDict


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
