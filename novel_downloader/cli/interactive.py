#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.interactive
--------------------------------

Interactive CLI mode for novel_downloader.
Supports multilingual prompt, input validation, and quit control.
"""

from novel_downloader.cli.lang import get_text


def interactive_main(lang: str = "zh") -> None:
    print(get_text("welcome", lang))
    print(get_text("quit_hint", lang))

    sites = ["起点", "笔趣阁"]

    while True:
        print("\n" + get_text("site_list", lang))
        for idx, site in enumerate(sites, 1):
            print(f"{idx}. {site}")

        choice = input(get_text("prompt_site", lang)).strip().lower()

        if choice in ["q", "quit", "exit", ""]:
            print(get_text("goodbye", lang))
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(sites)):
            print(get_text("invalid_choice", lang))
            continue

        site = sites[int(choice) - 1]
        print(get_text("you_chose_site", lang).format(site=site))
        # TODO: 接入后续搜索 / ID 输入 / 下载流程
    return
