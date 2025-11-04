#!/usr/bin/env python3
"""
novel_downloader.apps.cli.prompts
---------------------------------
"""

__all__ = [
    "select_books",
    "select_main_action",
    "select_search_result",
    "select_site",
]

from collections.abc import Sequence
from pathlib import Path

from novel_downloader.apps.cli import ui
from novel_downloader.apps.constants import DOWNLOAD_SUPPORT_SITES, SEARCH_SUPPORT_SITES
from novel_downloader.infra.i18n import t
from novel_downloader.schemas import SearchResult


def select_main_action() -> str:
    """
    Display the main interactive menu and return user's choice.
    """
    ui.render_table(
        t("Main Menu"),
        [t("#"), t("Action")],
        [
            ["1", t("Search for novels")],
            ["2", t("Download novel (by URL or Site/Book ID)")],
            ["3", t("Export previously downloaded novels")],
            ["", t("Exit")],
        ],
    )

    choice = ui.prompt_choice(
        t("Select an action"),
        ["1", "2", "3"],
    )
    return choice


def select_site(raw_dir: Path, per_page: int = 10) -> str | None:
    if not raw_dir.exists():
        ui.error(t("Raw data directory does not exist: {p}").format(p=str(raw_dir)))
        return None

    site_dirs = sorted([p for p in raw_dir.iterdir() if p.is_dir()])
    if not site_dirs:
        ui.warn(t("No sites found under {p}.").format(p=str(raw_dir)))
        return None

    all_rows = [
        [str(i), DOWNLOAD_SUPPORT_SITES.get(p.name, p.name), p.name]
        for i, p in enumerate(site_dirs, 1)
    ]

    total = len(all_rows)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = 1

    while True:
        start = (page - 1) * per_page + 1
        end = min(page * per_page, total)
        page_rows = all_rows[start - 1 : end]

        ui.render_table(
            t("Available Sites · Page {page}/{total}").format(
                page=page, total=total_pages
            ),
            [t("#"), t("Site Name"), t("Site Key")],
            page_rows,
        )

        numeric_choices = [str(i) for i in range(start, end + 1)]
        nav_choices = []
        if page < total_pages:
            nav_choices.append("n")
        if page > 1:
            nav_choices.append("p")

        choice = ui.prompt_choice(
            t(
                "Enter a number, 'n' for next, 'p' for previous (press Enter to cancel)"  # noqa: E501
            ),
            numeric_choices + nav_choices,
        )

        if choice == "":
            return None
        if choice == "n" and page < total_pages:
            page += 1
            continue
        if choice == "p" and page > 1:
            page -= 1
            continue
        if choice in numeric_choices:
            idx = int(choice)
            return site_dirs[idx - 1].name


def select_books(raw_dir: Path, site: str, per_page: int = 10) -> list[str]:
    import json

    site_dir = raw_dir / site
    if not site_dir.exists():
        ui.error(t("Site directory does not exist: {p}").format(p=str(site_dir)))
        return []

    book_dirs = sorted([p for p in site_dir.iterdir() if p.is_dir()])
    if not book_dirs:
        ui.warn(t("No books found under site '{site}'.").format(site=site))
        return []

    all_rows = []
    for i, p in enumerate(book_dirs, 1):
        book_id = p.name
        book_name, author = "", ""
        info_path = p / "book_info.raw.json"
        if info_path.exists():
            try:
                with info_path.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
                    book_name = str(meta.get("book_name", "") or "")
                    author = str(meta.get("author", "") or "")
            except Exception:
                ui.warn(t("Failed to read metadata for {bid}").format(bid=book_id))
        all_rows.append([str(i), book_id, book_name, author])

    total = len(all_rows)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = 1

    while True:
        start = (page - 1) * per_page + 1
        end = min(page * per_page, total)
        page_rows = all_rows[start - 1 : end]

        ui.render_table(
            t("Available Books for {site} · Page {page}/{total}").format(
                site=site, page=page, total=total_pages
            ),
            [t("#"), t("Book ID"), t("Title"), t("Author")],
            page_rows,
        )

        numeric_choices = [str(i) for i in range(start, end + 1)]
        nav_choices = []
        if page < total_pages:
            nav_choices.append("n")
        if page > 1:
            nav_choices.append("p")

        choice = ui.prompt_choice(
            t(
                "Enter numbers (e.g. 1,3,5), 'a' for all, 'n' next, 'p' previous (Enter to cancel)"  # noqa: E501
            ),
            numeric_choices + nav_choices + ["a"],
        )

        if choice == "":
            return []
        if choice == "a":
            return [p.name for p in book_dirs]
        if choice == "n" and page < total_pages:
            page += 1
            continue
        if choice == "p" and page > 1:
            page -= 1
            continue
        if "," in choice or choice in numeric_choices:
            try:
                idxs = sorted({int(s) for s in choice.split(",") if s.strip()})
            except ValueError:
                ui.warn(t("Invalid input."))
                continue
            if any(i < 1 or i > len(book_dirs) for i in idxs):
                ui.warn(t("One or more indices out of range."))
                continue
            return [book_dirs[i - 1].name for i in idxs]


def select_search_result(
    results: Sequence[SearchResult],
    per_page: int = 10,
) -> SearchResult | None:
    """
    Show results in pages and let user select by global index.
    """
    if not results:
        ui.warn(t("No results found."))
        return None

    total = len(results)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = 1

    columns = [
        t("#"),
        t("Title"),
        t("Author"),
        t("Latest"),
        t("Updated"),
        t("Site Name"),
        t("Book ID"),
    ]
    all_rows = [
        [
            str(i),
            r["title"],
            r["author"],
            r["latest_chapter"],
            r["update_date"],
            SEARCH_SUPPORT_SITES.get(r["site"], r["site"]),
            r["book_id"],
        ]
        for i, r in enumerate(results, 1)
    ]

    while True:
        start = (page - 1) * per_page + 1
        end = min(page * per_page, total)

        page_rows = all_rows[start - 1 : end]

        ui.render_table(
            t("Search Results · Page {page}/{total_pages}").format(
                page=page, total_pages=total_pages
            ),
            columns,
            page_rows,
        )

        numeric_choices = [str(i) for i in range(start, end + 1)]
        nav_choices = []
        if page < total_pages:
            nav_choices.append("n")
        if page > 1:
            nav_choices.append("p")

        choice = ui.prompt_choice(
            t(
                "Enter a number, 'n' for next, 'p' for previous (press Enter to cancel)"  # noqa: E501
            ),
            numeric_choices + nav_choices,
        )

        if choice == "":
            return None  # cancel
        if choice == "n" and page < total_pages:
            page += 1
            continue
        if choice == "p" and page > 1:
            page -= 1
            continue
        if choice in numeric_choices:
            idx = int(choice)
            return results[idx - 1]
