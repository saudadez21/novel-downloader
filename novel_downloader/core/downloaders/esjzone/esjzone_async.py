#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.esjzone.esjzone_async
-------------------------------------------------------

"""

from novel_downloader.config.models import DownloaderConfig
from novel_downloader.core.downloaders.common import CommonAsyncDownloader
from novel_downloader.core.interfaces import (
    AsyncRequesterProtocol,
    ParserProtocol,
    SaverProtocol,
)
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import async_sleep_with_random_delay


class EsjzoneAsyncDownloader(CommonAsyncDownloader):
    """"""

    def __init__(
        self,
        requester: AsyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "esjzone")

    async def _async_login(self) -> bool:
        """
        Restore cookies persisted by the session-based workflow.
        """
        print("session login async called")
        self._is_logged_in = False
        cookies: dict[str, str] = state_mgr.get_cookies(self._site)

        try:
            if await self._requester.login(cookies=cookies):
                self._is_logged_in = True
                return True
        except Exception as e:
            self.logger.warning("Cookie login failed for site %s: %s", self._site, e)

        username = self.config.username
        password = self.config.password
        print(f"user = {username} ; pass = {password}")
        if not (username and password):
            self.logger.warning(
                "Username or password not configured for site %s", self._site
            )
            return False

        MAX_RETRIES = 3
        wait_time = self.config.request_interval
        for _ in range(MAX_RETRIES):
            try:
                if await self._requester.login(username=username, password=password):
                    self._is_logged_in = True
                    return True
            except Exception:
                pass

            await async_sleep_with_random_delay(
                wait_time,
                mul_spread=1.1,
                max_sleep=wait_time + 2,
            )
        self.logger.warning("All login attempts failed for site %s", self._site)
        return False

    async def _finalize(self) -> None:
        """
        Save cookies to the state manager before closing.
        """
        if self.login_required:
            state_mgr.set_cookies(self._site, self._requester.cookies)
        return
