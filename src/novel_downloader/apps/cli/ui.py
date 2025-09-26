#!/usr/bin/env python3
"""
novel_downloader.apps.cli.ui
----------------------------

A small set of Rich-based helpers to keep CLI presentation and prompts
consistent across subcommands.

Public API:
  * info, success, warn, error
  * confirm
  * prompt, prompt_password
  * render_table
  * select_index
  * print_progress
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Iterable, Sequence
from logging.handlers import TimedRotatingFileHandler

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.status import Status

from novel_downloader.infra.paths import LOGGER_DIR, PACKAGE_NAME

_MUTE_LOGGERS: set[str] = {
    "fontTools.ttLib.tables._p_o_s_t",
}
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


def status(message: str) -> Status:
    """Context manager to show a spinner with a message."""
    return _CONSOLE.status(f"[bold cyan]{message}[/]", spinner="dots")


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
        result: str = Prompt.ask(message, default=default or "", show_default=False)
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
    from rich.table import Table

    table = Table(title=title, show_lines=True, expand=True)
    for col in columns:
        table.add_column(col, overflow="fold")
    for row in rows:
        table.add_row(*[str(x) for x in row])
    _CONSOLE.print(table)


def prompt_choice(prompt_text: str, choices: Sequence[str]) -> str:
    """
    Prompt user to select one of several choices.

    :param prompt_text: Prompt message shown to the user.
    :param choices: Valid choices (strings). Empty string is treated as cancel.
    :return: The raw user input, lowercased and trimmed. Returns "" if cancelled.
    """
    resp: str = Prompt.ask(
        prompt_text,
        choices=list(choices) + [""],
        show_choices=False,
        default="",
        show_default=False,
    )
    return resp.strip().lower()


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


def create_progress_hook(
    prefix: str = "Progress",
    unit: str = "item",
) -> tuple[Callable[[int, int], Awaitable[None]], Callable[[], None]]:
    from rich.progress import Progress, TaskID

    progress = Progress(console=_CONSOLE)
    task_id: TaskID | None = None

    async def hook(done: int, total: int) -> None:
        nonlocal task_id
        if task_id is None:
            progress.start()
            task_id = progress.add_task(f"[cyan]{prefix}[/]", total=max(1, total))

        progress.update(
            task_id,
            completed=done,
            total=max(1, total),
            description=f"{prefix} ({done}/{total} {unit})",
        )

    def close() -> None:
        progress.stop()

    return hook, close


def _normalize_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return logging._nameToLevel.get(level.upper(), logging.INFO)
    return logging.INFO


def setup_logging(
    console_level: int | str = "INFO",
    file_level: int | str = "DEBUG",
    *,
    console: bool = True,
    file: bool = True,
    backup_count: int = 7,
    when: str = "midnight",
) -> None:
    # Tame noisy third-party loggers
    for name in _MUTE_LOGGERS:
        ml = logging.getLogger(name)
        ml.setLevel(logging.ERROR)
        ml.propagate = False

    logger = logging.getLogger(PACKAGE_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # otherwise may affected by PaddleOCR

    # Clear existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler (rotates daily)
    if file:
        file_level = _normalize_level(file_level)

        LOGGER_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGGER_DIR / f"{PACKAGE_NAME}.log"

        fh = TimedRotatingFileHandler(
            filename=log_path,
            when=when,
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
            utc=False,
            delay=True,
        )

        file_formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(file_formatter)
        fh.setLevel(file_level)
        logger.addHandler(fh)

        print(f"Logging to {log_path}")

    # Console handler
    if console:
        from rich.logging import RichHandler

        console_level = _normalize_level(console_level)

        ch = RichHandler(
            console=_CONSOLE,
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_path=False,
            log_time_format="%H:%M:%S",
        )
        ch.setFormatter(logging.Formatter("%(message)s"))
        ch.setLevel(console_level)
        logger.addHandler(ch)
