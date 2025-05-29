#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.sfacg.sfacg_sync
--------------------------------------------------

"""

from novel_downloader.config.models import DownloaderConfig
from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.interfaces import (
    ParserProtocol,
    SaverProtocol,
    SyncRequesterProtocol,
)
from novel_downloader.utils.cookies import resolve_cookies
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr


class SfacgDownloader(CommonDownloader):
    """"""

    def __init__(
        self,
        requester: SyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "sfacg")

    def _session_login(self) -> bool:
        """
        Restore cookies persisted by the session-based workflow.
        """
        self._is_logged_in = False
        cookies: dict[str, str] = state_mgr.get_cookies(self._site)

        try:
            if self._requester.login(cookies=cookies):
                self._is_logged_in = True
                return True
        except Exception as e:
            self.logger.warning("Cookie login failed for site %s: %s", self._site, e)

        MAX_RETRIES = 3
        print(t("session_login_prompt_intro"))
        for attempt in range(1, MAX_RETRIES + 1):
            cookie_str = input(
                t(
                    "session_login_prompt_paste_cookie",
                    attempt=attempt,
                    max_retries=MAX_RETRIES,
                )
            ).strip()
            try:
                cookies = resolve_cookies(cookie_str)
                if self.requester.login(cookies=cookies):
                    return True
            except (ValueError, TypeError):
                print(t("session_login_prompt_invalid_cookie"))
        return False

    def _finalize(self) -> None:
        """
        Save cookies to the state manager before closing.
        """
        if self._requester.requester_type == "session" and self._login_required:
            state_mgr.set_cookies(self._site, self._requester.cookies)
        return
