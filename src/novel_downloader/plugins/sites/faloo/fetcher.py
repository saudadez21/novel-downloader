#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.faloo.fetcher
--------------------------------------------
"""

import base64
import re
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas.config import FetcherConfig


@registrar.register_fetcher()
class FalooFetcher(BaseFetcher):
    """
    A session class for interacting with the 飞卢小说网 (b.faloo.com) novel.
    """

    site_name: str = "faloo"

    BOOKCASE_URL = "https://u.faloo.com/UserFavoriate.aspx"
    BOOK_INFO_URL = "https://b.faloo.com/{book_id}.html"
    CHAPTER_URL = "https://b.faloo.com/{book_id}_{chapter_id}.html"

    COOKIE_GATE_RE = re.compile(r'cookie\s*=\s*"([^=]+)=([^";]+)', re.IGNORECASE)
    IMAGE_DO3_ARGS_RE = re.compile(r"image_do3\s*\(\s*(.*?)\s*\)", re.S)
    ARG_SPLIT_RE = re.compile(r"'[^']*'|[^,]+")

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(config, cookies, **kwargs)

        self._gate_cookies: set[str] = set()

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.BOOK_INFO_URL.format(book_id=book_id)
        attemt_1 = await self.fetch(url, **kwargs)

        gate = self._extract_cookie_gate(attemt_1)
        if gate:
            self._apply_gate_cookie(gate)
            attemt_2 = await self.fetch(url, **kwargs)
            return [attemt_2]

        return [attemt_1]

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
        raw_html = await self.fetch(url, **kwargs)
        gate = self._extract_cookie_gate(raw_html)
        if gate:
            self._apply_gate_cookie(gate)
            raw_html = await self.fetch(url, **kwargs)

        results: list[str] = [raw_html]
        vip_params_list = self._extract_vip_image_param(raw_html)
        if not vip_params_list:
            return results

        vip_params_list.sort(key=lambda d: int(d.get("num", 0)))
        for vip_params in vip_params_list:
            domain = "https://read.faloo.com/"
            if vip_params["ct"] == "0":
                domain = "https://read6.faloo.com/"

            img_url = domain + "Page4VipImage.aspx"
            resp = await self.session.get(img_url, params=vip_params)
            if not resp.ok:
                raise ConnectionError(
                    f"Image request failed: {img_url} status={resp.status}"
                )

            img_base64 = base64.b64encode(resp.content).decode("utf-8")
            results.append(img_base64)

        return results

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        return [await self.fetch(self.BOOKCASE_URL, **kwargs)]

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        logged_out_keywords = [
            "获取手机验证码",
            "用户登录",
            "还没有账号？",
        ]
        logged_in_keywords = [
            "我的书架",
            "我的主页",
        ]

        resp_list = await self.get_bookcase()
        if not resp_list:
            return False
        resp_text = resp_list[0]

        if any(kw in resp_text for kw in logged_out_keywords):
            return False
        if any(kw in resp_text for kw in logged_in_keywords):
            return True

        return False

    @classmethod
    def _extract_cookie_gate(cls, html: str) -> tuple[str, str] | None:
        m = cls.COOKIE_GATE_RE.search(html)
        if not m:
            return None
        name, value = m.group(1), m.group(2)
        return name, value

    def _apply_gate_cookie(self, gate: tuple[str, str]) -> None:
        """
        Replace previously-set Faloo anti-bot cookies with the new one.
        """
        name, value = gate

        for old_name in list(self._gate_cookies):
            self.session.clear_cookie(old_name)
            self._gate_cookies.remove(old_name)

        self.session.update_cookies({name: value})
        self._gate_cookies.add(name)

    @classmethod
    def _extract_vip_image_param(cls, html_str: str) -> list[dict[str, str]]:
        """
        Extract ALL sets of the first 14 args passed to image_do3(...).

        :return: empty list if none found.
        """
        matches = cls.IMAGE_DO3_ARGS_RE.findall(html_str)
        if not matches:
            return []  # not VIP

        params_list: list[dict[str, str]] = []
        for args_str in matches:
            raw_args = [a.strip() for a in cls.ARG_SPLIT_RE.findall(args_str)]

            # remove surrounding quotes
            args_clean = [
                a[1:-1] if a.startswith("'") and a.endswith("'") else a
                for a in raw_args
            ]

            # need at least 14 args
            if len(args_clean) < 14:
                continue

            args_clean = args_clean[:14]

            (
                num,
                o,
                id_,
                n,
                en,
                t,
                k,
                u,
                time,
                fontsize,
                fontcolor,
                chaptertype,
                font_family_type,
                background_type,
            ) = args_clean

            params_list.append(
                {
                    "num": num,
                    "o": o,
                    "id": id_,
                    "n": n,
                    "ct": chaptertype,
                    "en": en,
                    "t": t,
                    "font_size": fontsize,
                    "font_color": fontcolor,
                    "FontFamilyType": font_family_type,
                    "backgroundtype": background_type,
                    "u": u,
                    "time": time,
                    "k": k,
                }
            )

        return params_list
