#!/usr/bin/env python3
"""
A simple ESJZone login script using Playwright.
"""

import argparse
import sys
from pathlib import Path

from platformdirs import user_config_path
from playwright.sync_api import (
    Page,
    ViewportSize,
    sync_playwright,
)

APP_DIR_NAME = "novel_downloader"
BASE_CONFIG_DIR = user_config_path(APP_DIR_NAME, appauthor=False)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_CONFIG_DIR / "data"
BROWSER_DATA_DIR = SCRIPT_DIR / "browser_data"
COOKIES_FILENAME = "session_state.cookies"
DEFAULT_TIMEOUT = 30 * 1_000  # milliseconds

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
)
_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
window.chrome = { runtime: {} };
""".strip()

LOGIN_URL = "https://www.esjzone.cc/my/login"
BOOKCASE_URL = "https://www.esjzone.cc/my/favorite"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Log in to ESJZone and save session cookies"
    )
    p.add_argument(
        "-u",
        "--user-name",
        type=str,
        required=True,
        help="ESJZone account email",
    )
    p.add_argument(
        "-p",
        "--password",
        type=str,
        required=True,
        help="ESJZone password",
    )
    p.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory to store cookie files (default: {DEFAULT_DATA_DIR})",
    )
    p.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Navigation timeout in ms (default: {DEFAULT_TIMEOUT})",
    )
    return p.parse_args()


def _get_bookcase(page: Page) -> str:
    page.goto(BOOKCASE_URL)
    return page.content()


def _check_login_status(page: Page) -> bool:
    """
    Check whether the user is currently logged in by
    inspecting the bookcase page content.

    :return: True if the user is logged in, False otherwise.
    """
    keywords = [
        "window.location.href='/my/login'",
        "會員登入",
        "會員註冊 SIGN UP",
    ]
    resp_text = _get_bookcase(page)
    if not resp_text:
        return False
    return not any(kw in resp_text for kw in keywords)


def login(
    page: Page,
    username: str = "",
    password: str = "",
    attempt: int = 3,
) -> bool:
    # skip if already logged in
    if _check_login_status(page):
        print("[auth] Existing session is valid, skipping login.")
        return True

    if not (username and password):
        print("[auth] No credentials provided.")
        return False

    for i in range(1, attempt + 1):
        print(f"[auth] Attempt {i}/{attempt}...")
        page.goto(LOGIN_URL)
        page.fill('input[name="email"]', username)
        page.fill('input[name="pwd"]', password)
        page.click('a.btn-send[data-send="mem_login"]')
        page.wait_for_load_state("networkidle")
        if _check_login_status(page):
            print("[auth] Login succeeded.")
            return True

    print(f"[auth] Login failed after {attempt} attempts.")
    return False


def perform_login(
    state_file: Path,
    username: str = "",
    password: str = "",
    attempt: int = 3,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=False,
            user_agent=DEFAULT_USER_AGENT,
            locale="zh-CN",
            viewport=ViewportSize(width=1280, height=800),
            java_script_enabled=True,
        )
        context.set_default_timeout(timeout)
        context.add_init_script(_STEALTH_SCRIPT)

        page = context.new_page()
        ok = login(page, username=username, password=password, attempt=attempt)
        if ok:
            context.storage_state(path=state_file)
        page.close()
        context.close()
        return ok


def main() -> None:
    args = parse_args()

    state_file = args.data_dir / "esjzone" / COOKIES_FILENAME
    state_file.parent.mkdir(parents=True, exist_ok=True)

    success = perform_login(
        state_file=state_file,
        username=args.user_name,
        password=args.password,
        timeout=args.timeout,
    )

    if success:
        print(f"[auth] Session saved to {state_file}")
        sys.exit(0)
    else:
        print("[auth] Could not establish a session.")
        sys.exit(1)


if __name__ == "__main__":
    main()
