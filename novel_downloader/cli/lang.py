#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.lang
--------------------------

Multilingual text dictionary and utility for CLI and interactive mode.

This module provides a centralized interface for internationalization (i18n)
by defining text content for both English and Chinese. It supports:

- CLI argument descriptions
- Interactive CLI prompts and messages
- Easy language switching via get_text()

Future plans may include integration with gettext or external .po/.mo files.
"""

LANGUAGES = {
    "en": {
        # CLI Labels
        "cli_desc": "Novel Downloader CLI",
        "help_interactive": "Enter interactive mode",
        "help_lang": "Interface language (default zh)",
        "help_site": "Target site (pinyin tag, default qidian)",
        "help_config": "Path to config file (default: defaults/base.yaml)",
        "help_book_id": "Book IDs to download, overrides book_ids in config",
        "msg_lang_saved": "Language preference saved",
        "label_site": "Target site",
        "label_config": "Config path",
        "label_book_ids": "Book IDs",
        # Interactive
        "welcome": "Welcome to the novel downloader (interactive mode)",
        "quit_hint": "Enter q / quit / blank to exit.",
        "site_list": "Available sites:",
        "prompt_site": "Choose a site by number: ",
        "invalid_choice": "Invalid input. Please enter a valid number.",
        "you_chose_site": "You chose: {site}",
        "goodbye": "Thanks for using, goodbye!",
    },
    "zh": {
        # CLI Labels
        "cli_desc": "小说下载器",
        "help_interactive": "进入交互模式",
        "help_lang": "界面语言 (默认 zh)",
        "help_site": "目标站点 (拼音标签, 默认 qidian)",
        "help_config": "配置文件路径, 默认为项目内的 defaults/base.yaml",
        "help_book_id": "指定下载的小说 book_id, 可输入多个",
        "msg_lang_saved": "语言设置已保存",
        "label_site": "下载站点",
        "label_config": "配置路径",
        "label_book_ids": "小说 ID 列表",
        # Interactive
        "welcome": "欢迎使用小说下载器 (CLI 交互模式)",
        "quit_hint": "输入 q / quit / 空行 可退出程序。",
        "site_list": "可选择的站点：",
        "prompt_site": "选择站点编号: ",
        "invalid_choice": "输入无效, 请重新输入编号。",
        "you_chose_site": "您选择了站点：{site}",
        "goodbye": "感谢使用, 再见!",
    },
}


def get_text(key: str, lang: str = "en") -> str:
    """
    Retrieve a localized string by key and language.

    :param key: The string key.
    :param lang: The language code ('en' or 'zh').
    :return: The translated string, or the key if not found.
    """
    return LANGUAGES.get(lang, LANGUAGES["en"]).get(key, key)
