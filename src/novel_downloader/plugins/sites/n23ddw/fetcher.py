#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23ddw.fetcher
---------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N23ddwSession(GenericSession):
    """
    A session class for interacting with the 顶点小说网 (www.23ddw.net) novel.
    """

    site_name: str = "n23ddw"

    BASE_URL = "https://www.23ddw.net"
    BOOK_INFO_URL = "https://www.23ddw.net/du/{book_id}/"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/du/{book_id}/{chapter_id}.html"
            if idx == 1
            else f"/du/{book_id}/{chapter_id}_{idx}.html"
        )
