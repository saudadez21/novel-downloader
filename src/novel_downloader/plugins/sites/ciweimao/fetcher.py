#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciweimao.fetcher
-----------------------------------------------
"""

import base64
import logging
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.ciweimao.my_encryt import my_decrypt

logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class CiweimaoFetcher(BaseFetcher):
    """
    A session class for interacting with 刺猬猫 (www.ciweimao.com).
    """

    site_name: str = "ciweimao"

    BASE_URL = "https://www.ciweimao.com"
    BOOK_INFO_URL = "https://www.ciweimao.com/book/{book_id}"
    CHAPTER_URL = "https://www.ciweimao.com/chapter/{chapter_id}"

    BOOKCASE_URL = "https://www.ciweimao.com/bookshelf/my_book_shelf/"

    CHAPTER_LIST_URL = (
        "https://www.ciweimao.com/chapter/get_chapter_list_in_chapter_detail"
    )

    IMAGE_SESSION_URL = "https://www.ciweimao.com/chapter/ajax_get_image_session_code"
    VIP_IMAGE_URL = "https://www.ciweimao.com/chapter/book_chapter_image"
    SESSION_URL = "https://www.ciweimao.com/chapter/ajax_get_session_code"
    DETAIL_URL = "https://www.ciweimao.com/chapter/get_book_chapter_detail_info"
    CHAPTER_IMAGE_LIST_URL = (
        "https://www.ciweimao.com/chapter/chapter_image_tsukkomi_list"
    )

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        raw_page = await self.fetch(info_url, **kwargs)
        results: list[str] = [raw_page]

        ajax_headers = {
            "Accept": "text/html, */*; q=0.01",
            "Referer": info_url,
            "Origin": self.BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
        }
        list_resp = await self.session.post(
            self.CHAPTER_LIST_URL,
            headers=ajax_headers,
            data={"book_id": book_id, "chapter_id": "0", "orderby": "0"},
        )

        if not list_resp.ok:
            logger.warning("Request failed (chapter list) HTTP %s", list_resp.status)
            return []

        results.append(list_resp.text)
        return results

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Layout:

        * text chapter:
            [ html_page, chapter_detail_json, session_code_json ]
        * image chapter:
            [ html_page, image_base64, image_list_json ]
        """
        chap_url = self.CHAPTER_URL.format(chapter_id=chapter_id)
        raw_page = await self.fetch(chap_url, **kwargs)
        results: list[str] = [raw_page]

        is_image_chapter = "J_ImgRead" in raw_page

        # common headers
        ajax_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": chap_url,
            "Origin": self.BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
        }
        image_headers = {
            "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": chap_url,
            "Origin": self.BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
        }

        if is_image_chapter:
            # -------- image / VIP chapter flow --------
            sess_resp = await self.session.post(
                self.IMAGE_SESSION_URL,
                headers=ajax_headers,
            )

            if not sess_resp.ok:
                logger.warning(
                    "Request failed (image session code) HTTP %s", sess_resp.status
                )
                return []

            image_session_obj = sess_resp.json()

            if image_session_obj.get("code") != 100000:
                logger.warning("image session code error: %s", image_session_obj)
                return []

            image_code_plain = my_decrypt(
                content=image_session_obj["image_code"],
                keys=image_session_obj["encryt_keys"],
                access_key=image_session_obj["access_key"],
            )

            vip_image_params = {
                "chapter_id": chapter_id,
                "area_width": "871",
                "font": "undefined",
                "font_size": "18",
                "image_code": image_code_plain,
                "bg_color_name": "white",
                "text_color_name": "white",
            }

            img_resp = await self.session.get(
                self.VIP_IMAGE_URL,
                params=vip_image_params,
                headers=image_headers,
            )

            if not img_resp.ok or not img_resp.content:
                logger.warning(
                    "Request failed or empty (vip image) HTTP %s", img_resp.status
                )
                return []

            img_b64 = base64.b64encode(img_resp.content).decode("ascii")

            img_list_params = {
                "chapter_id": chapter_id,
                "area_width": "871",
                "font_size": "18",
            }
            img_list_resp = await self.session.get(
                self.CHAPTER_IMAGE_LIST_URL,
                params=img_list_params,
                headers=ajax_headers,
            )

            if not img_list_resp.ok or not img_list_resp.content:
                logger.warning(
                    "Request failed or empty (image list) HTTP %s", img_list_resp.status
                )
                return []

            results.append(img_b64)
            results.append(img_list_resp.text)

            return results

        # -------- text chapter flow --------
        session_headers = {
            **ajax_headers,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }

        # 1) get chapter_access_key
        sess_resp = await self.session.post(
            self.SESSION_URL,
            headers=session_headers,
            data={"chapter_id": chapter_id},
        )

        if not sess_resp.ok:
            logger.warning("Request failed (session code) HTTP %s", sess_resp.status)
            return []

        session_json_str = sess_resp.text
        session_obj = sess_resp.json()

        chapter_access_key = session_obj.get("chapter_access_key")
        if not chapter_access_key:
            logger.warning("No chapter_access_key in session response: %s", session_obj)
            return results

        # 2) get chapter detail info
        detail_resp = await self.session.post(
            self.DETAIL_URL,
            headers=session_headers,
            data={
                "chapter_id": chapter_id,
                "chapter_access_key": chapter_access_key,
            },
        )

        if not detail_resp.ok:
            logger.warning(
                "Request failed (chapter detail) HTTP %s", detail_resp.status
            )
            return []

        detail_json_str = detail_resp.text

        results.append(detail_json_str)
        results.append(session_json_str)
        return results

    async def fetch_bookcase(self, **kwargs: Any) -> list[str]:
        return [await self.fetch(self.BOOKCASE_URL, **kwargs)]

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "邮箱验证码登录",
            "账户登录",
        ]
        resp_text = await self.fetch_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)
