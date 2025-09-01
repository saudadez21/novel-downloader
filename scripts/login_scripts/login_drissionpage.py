#!/usr/bin/env python3
"""
CLI helper to perform manual login via DrissionPage and persist session
cookies + storage for later automated downloading.
"""

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from DrissionPage import ChromiumOptions, ChromiumPage
from platformdirs import user_config_path

SITE_LOGIN_MAP = {
    "esjzone": "https://www.esjzone.cc/my/login",
    "qidian": "https://passport.qidian.com/",
    "sfacg": "https://m.sfacg.com/login",
    "yamibo": "https://www.yamibo.com/user/login",
}
SITE_HOME_MAP = {
    "qidian": "https://www.qidian.com/",
}

APP_DIR_NAME = "novel_downloader"
BASE_CONFIG_DIR = user_config_path(APP_DIR_NAME, appauthor=False)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_CONFIG_DIR / "data"
BROWSER_DATA_DIR = SCRIPT_DIR / "browser_data"
STATE_FILENAME = "session_state.cookies"
DEFAULT_TIMEOUT = 30  # seconds


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

      * `site`: which site to log in to (must be one of SITE_MAP keys)
      * `--data-dir`: where to store cookie files
      * `--timeout`: navigation timeout in milliseconds
    """
    p = argparse.ArgumentParser(
        description="Log in to a novel site and save session cookies."
    )
    p.add_argument(
        "site",
        choices=SITE_LOGIN_MAP.keys(),
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


def save_playwright_state(page: ChromiumPage, state_path: Path) -> None:
    """
    Export cookies, localStorage, and sessionStorage from DrissionPage
    and save them as a Playwright-compatible storage state JSON.
    """
    cookies_json = page.cookies(all_domains=True, all_info=True).as_json()
    cookies = json.loads(cookies_json)

    parsed = urlparse(page.url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    raw_session = page.session_storage()
    raw_local = page.local_storage()

    if isinstance(raw_session, dict):
        session_dict: dict[str, Any] = raw_session
    else:
        session_dict = {}
    if isinstance(raw_local, dict):
        local_dict: dict[str, Any] = raw_local
    else:
        local_dict = {}

    session_items = [{"name": k, "value": v} for k, v in session_dict.items()]
    local_items = [{"name": k, "value": v} for k, v in local_dict.items()]

    state = {
        "cookies": cookies,
        "origins": [
            {
                "origin": origin,
                "localStorage": local_items,
                "sessionStorage": session_items,
            }
        ],
    }

    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def perform_login(site_key: str, state_path: Path, timeout: int) -> None:
    """
    Launch a DrissionPage browser with persistent profile, navigate to login_url,
    wait for user to log in manually, then save Playwright storage state.
    """
    BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    options = ChromiumOptions().set_user_data_path(str(BROWSER_DATA_DIR))
    page = ChromiumPage(options)

    login_url = SITE_LOGIN_MAP[site_key]
    page.get(login_url, timeout=timeout)

    print(">> Complete login in the browser, then press Enter to continue.")
    print(">> 完成登录后, 请按回车继续")
    try:
        input()
    except KeyboardInterrupt:
        print("Login interrupted. No state was saved.")
        print("中断: 未保存任何新会话状态")
        page.quit()
        return

    home_url = SITE_HOME_MAP.get(site_key)
    if home_url:
        page.get(home_url, timeout=timeout)

    save_playwright_state(page, state_path)
    print("Session state successfully saved.")
    print("会话状态已保存")

    page.quit()


def main() -> None:
    args = parse_args()
    site_key = args.site
    state_file = args.data_dir / site_key / STATE_FILENAME
    state_file.parent.mkdir(parents=True, exist_ok=True)

    perform_login(site_key, state_file, args.timeout)


if __name__ == "__main__":
    main()
