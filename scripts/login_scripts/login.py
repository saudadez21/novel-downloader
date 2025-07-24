#!/usr/bin/env python3
"""
CLI helper to perform manual login via Playwright and persist session cookies
for later automated downloading.
"""

import argparse
from pathlib import Path

from platformdirs import user_config_path
from playwright.sync_api import (
    Playwright,
    ViewportSize,
    sync_playwright,
)

SITE_MAP = {
    "esjzone": "https://www.esjzone.cc/my/login",
    "qidian": "https://passport.qidian.com/",
    "sfacg": "https://m.sfacg.com/login",
    "yamibo": "https://www.yamibo.com/user/login",
}

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


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    - site: which site to log in to (must be one of SITE_MAP keys)
    - --data-dir: where to store cookie files
    - --timeout: navigation timeout in milliseconds
    """
    p = argparse.ArgumentParser(
        description="Log in to a novel site and save session cookies."
    )
    p.add_argument(
        "site",
        choices=SITE_MAP.keys(),
        help="Which site to log in to.",
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
        help=f"Navigation timeout in ms (default: {DEFAULT_TIMEOUT}).",
    )
    return p.parse_args()


def login(
    playwright: Playwright,
    login_url: str,
    state_file: Path,
    timeout: int,
) -> None:
    """
    Open a browser window pointed at `login_url`, let the user log in manually,
    then save the storage state (cookies, localStorage) to `state_file`.

    :param playwright: active Playwright instance
    :param login_url: URL to navigate for login
    :param state_file: path to write storage_state JSON
    :param timeout: default timeout for navigation/actions, in ms
    """
    context = playwright.chromium.launch_persistent_context(
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
    page.goto(login_url)

    print(">> Complete login in the browser, then press Enter to continue.")
    print(">> 完成登录后, 请按回车继续")
    try:
        input()
    except KeyboardInterrupt:
        print("Login interrupted. No state was saved.")
        print("中断: 未保存任何新会话状态")
    else:
        # Persist cookies + localStorage
        context.storage_state(path=state_file)
        print("Session state successfully saved.")
        print("会话状态已保存")

    page.close()
    context.close()


def main() -> None:
    args = parse_args()
    site_key = args.site
    login_url = SITE_MAP[site_key]
    state_file = args.data_dir / site_key / COOKIES_FILENAME
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        login(
            playwright=pw,
            login_url=login_url,
            state_file=state_file,
            timeout=args.timeout,
        )
    return


if __name__ == "__main__":
    main()
