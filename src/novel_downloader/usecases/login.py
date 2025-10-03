#!/usr/bin/env python3
"""
novel_downloader.usecases.login
-------------------------------
"""

from novel_downloader.plugins.protocols import FetcherProtocol

from .protocols import LoginUI


async def ensure_login(
    fetcher: FetcherProtocol,
    login_ui: LoginUI,
    login_config: dict[str, str] | None = None,
) -> bool:
    if await fetcher.load_state():
        return True

    login_data = await login_ui.prompt(fetcher.login_fields, login_config)
    if not await fetcher.login(**login_data):
        login_ui.on_login_failed()
        return False

    await fetcher.save_state()
    login_ui.on_login_success()
    return True
