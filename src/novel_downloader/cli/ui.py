#!/usr/bin/env python3
"""
novel_downloader.cli.ui
-----------------------

A small set of Rich-based helpers to keep CLI presentation and prompts
consistent across subcommands.

Public API:
- info, success, warn, error
- confirm
- prompt, prompt_password
- render_table
- select_index
- print_progress
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

_CONSOLE = Console()


def info(message: str) -> None:
    """Print a neutral informational message."""
    _CONSOLE.print(message)


def success(message: str) -> None:
    """Print a success message in a friendly color."""
    _CONSOLE.print(f"[green]{message}[/]")


def warn(message: str) -> None:
    """Print a warning message."""
    _CONSOLE.print(f"[yellow]{message}[/]")


def error(message: str) -> None:
    """Print an error message."""
    _CONSOLE.print(f"[red]{message}[/]")


def confirm(message: str, *, default: bool = False) -> bool:
    """
    Ask a yes/no question.

    :param message: The question to display (without [y/N] suffix).
    :param default: Default choice (pressing Enter = Yes if True, No if False).
    :return: True if user confirms (Yes), otherwise False.
    """
    try:
        result: bool = Confirm.ask(f"[bold]{message}[/bold]", default=default)
        return result
    except (KeyboardInterrupt, EOFError):
        warn("Cancelled.")
        return False


def prompt(message: str, *, default: str | None = None) -> str:
    """
    Prompt user for a line of text.

    :param message: Prompt message.
    :param default: Default value if the user presses Enter.
    :return: The user's input.
    """
    try:
        result: str = Prompt.ask(message, default=default or "")
        return result
    except (KeyboardInterrupt, EOFError):
        warn("Cancelled.")
        return default or ""


def prompt_password(message: str) -> str:
    """
    Prompt user for a password/secret value (no echo).

    :param message: Prompt message.
    :return: The user's input (may be empty).
    """
    try:
        result: str = Prompt.ask(message, password=True)
        return result
    except (KeyboardInterrupt, EOFError):
        warn("Cancelled.")
        return ""


def render_table(
    title: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[str]],
) -> None:
    """
    Render a simple full-width table.

    :param title: Table title.
    :param columns: Column names.
    :param rows: Row data; each row must have the same length as `columns`.
    """
    table = Table(title=title, show_lines=True, expand=True)
    for col in columns:
        table.add_column(col, overflow="fold")
    for row in rows:
        table.add_row(*[str(x) for x in row])
    _CONSOLE.print(table)


def select_index(prompt_text: str, total: int) -> int | None:
    """
    Prompt user to select an index in [1..total]. Empty input cancels.

    :param prompt_text: Displayed prompt (e.g., 'Select index').
    :param total: Maximum valid index (minimum is 1).
    :return: Selected 1-based index, or None if user cancels.
    """
    if total <= 0:
        return None
    valid_choices = [str(i) for i in range(1, total + 1)]
    choice = Prompt.ask(
        prompt_text,
        choices=valid_choices + [""],
        show_choices=False,
        default="",
        show_default=False,
    ).strip()
    if not choice:
        return None
    return int(choice)


def print_progress(
    done: int,
    total: int,
    *,
    prefix: str = "Progress",
    unit: str = "item",
) -> None:
    """
    Print a lightweight progress line.

    :param done: Completed count.
    :param total: Total count.
    :param prefix: Text prefix shown before numbers.
    :param unit: Logical unit name (e.g., 'item').
    """
    total = max(1, total)
    pct = done / total * 100.0
    _CONSOLE.print(f"[dim]{prefix}[/] {done}/{total} {unit} ({pct:.2f}%)")
