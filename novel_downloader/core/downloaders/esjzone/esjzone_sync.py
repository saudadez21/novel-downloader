#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.esjzone.esjzone_sync
------------------------------------------------------

"""

from novel_downloader.config.models import DownloaderConfig
from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.interfaces import (
    ParserProtocol,
    SaverProtocol,
    SyncRequesterProtocol,
)
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import sleep_with_random_delay


class EsjzoneDownloader(CommonDownloader):
    """"""

    def __init__(
        self,
        requester: SyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "esjzone")

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

        username = self.config.username
        password = self.config.password
        if not (username and password):
            self.logger.warning(
                "Username or password not configured for site %s", self._site
            )
            return False

        MAX_RETRIES = 3
        wait_time = self.config.request_interval
        for _ in range(MAX_RETRIES):
            try:
                if self._requester.login(username=username, password=password):
                    self._is_logged_in = True
                    return True
            except Exception:
                pass

            sleep_with_random_delay(
                wait_time,
                mul_spread=1.1,
                max_sleep=wait_time + 2,
            )
        self.logger.warning("All login attempts failed for site %s", self._site)
        return False

    def _finalize(self) -> None:
        """
        Save cookies to the state manager before closing.
        """
        if self._requester.requester_type == "session" and self._login_required:
            state_mgr.set_cookies(self._site, self._requester.cookies)
        return
