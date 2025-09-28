#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.parser
--------------------------------------------

"""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from html import unescape
from pathlib import Path
from typing import Any, TypedDict

from lxml import html

from novel_downloader.infra.cookies import get_cookie_value
from novel_downloader.infra.fontocr import get_font_ocr
from novel_downloader.infra.jsbridge import get_decryptor
from novel_downloader.infra.paths import DATA_DIR
from novel_downloader.libs.textutils import truncate_half_lines
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    ParserConfig,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


class Rule(TypedDict, total=False):
    delete_all: bool
    delete_first: bool
    transform_flip_x: bool
    append_start_char: str
    append_end_char: str
    append_start_attr: str
    append_end_attr: str


class Rules(TypedDict):
    # e.g., orders = ["i", "em", "span"]
    orders: list[str]
    # e.g., sy["sy-3"] -> Rule
    sy: dict[str, Rule]
    # e.g., p_rules["p3"]["i"] -> Rule
    p_rules: dict[str, dict[str, Rule]]


@registrar.register_parser()
class QidianParser(BaseParser):
    """
    Parser for 起点中文网 site.
    """

    site_name: str = "qidian"

    def __init__(self, config: ParserConfig, fuid: str = ""):
        """
        Initialize the QidianParser with the given configuration.
        """
        super().__init__(config)

        self._rand_path = self._base_cache_dir / "qidian" / "randomFont.ttf"
        self._fixed_font_dir = self._base_cache_dir / "qidian" / "fixed_fonts"
        self._fixed_map_dir = self._base_cache_dir / "qidian" / "fixed_font_map"
        self._debug_dir = Path.cwd() / "debug" / "qidian"

        self._state_files = [
            DATA_DIR / "qidian" / "session_state.cookies",
        ]
        self._fuid = fuid

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        doc = html.fromstring(html_list[0])

        # --- Book name ---
        book_name = self._first_str(doc.xpath('//h1[@id="bookName"]/text()'))
        if not book_name:
            book_name = self._first_str(
                doc.xpath('//meta[@property="og:novel:book_name"]/@content')
            )

        # --- Author ---
        author = self._first_str(doc.xpath('//a[@class="writer-name"]/text()'))
        if not author:
            author = self._first_str(
                doc.xpath('//meta[@property="og:novel:author"]/@content')
            )
        if not author:
            author = self._first_str(
                doc.xpath('//span[contains(@class,"author")]/text()'),
                replaces=[("作者:", "")],
            )

        # --- Book ID + cover ---
        book_id = doc.xpath('//a[@id="bookImg"]/@data-bid')[0]
        cover_url = f"https://bookcover.yuewen.com/qdbimg/349573/{book_id}/600.webp"

        # --- Update time ---
        update_time = self._first_str(
            doc.xpath('//span[@class="update-time"]/text()'),
            replaces=[("更新时间:", "")],
        )
        if not update_time:
            update_time = self._first_str(
                doc.xpath('//meta[@property="og:novel:update_time"]/@content')
            )

        # --- Status ---
        serial_status = self._first_str(
            doc.xpath('//p[@class="book-attribute"]/span[1]/text()')
        )
        if not serial_status:
            serial_status = self._first_str(
                doc.xpath('//meta[@property="og:novel:status"]/@content')
            )

        # --- Tags ---
        tags = [
            t.strip()
            for t in doc.xpath('//p[contains(@class,"all-label")]//a/text()')
            if t.strip()
        ]
        if not tags:
            # fallback meta category
            tag = self._first_str(
                doc.xpath('//meta[@property="og:novel:category"]/@content')
            )
            if tag:
                tags = [tag]

        # --- Word count ---
        word_count = self._first_str(doc.xpath('//p[@class="count"]/em[1]/text()'))

        # --- Summaries ---
        summary_brief = self._first_str(doc.xpath('//p[@class="intro"]/text()'))
        if not summary_brief:
            summary_brief = self._first_str(
                doc.xpath('//meta[@property="og:description"]/@content')
            )

        raw_lines = [
            s.strip()
            for s in doc.xpath('//p[@id="book-intro-detail"]//text()')
            if s.strip()
        ]
        summary = "\n".join(raw_lines) if raw_lines else summary_brief

        volumes: list[VolumeInfoDict] = []
        for vol in doc.xpath('//div[@id="allCatalog"]//div[@class="catalog-volume"]'):
            vol_name = self._first_str(vol.xpath('.//h3[@class="volume-name"]/text()'))
            vol_name = vol_name.split(chr(183))[0].strip()
            chapters: list[ChapterInfoDict] = []
            for li in vol.xpath('.//ul[contains(@class,"volume-chapters")]/li'):
                title = self._first_str(li.xpath('.//a[@class="chapter-name"]/text()'))
                url = self._first_str(li.xpath('.//a[@class="chapter-name"]/@href'))
                cid = url.rstrip("/").split("/")[-1] if url else ""
                chapters.append({"title": title, "url": url, "chapterId": cid})
            volumes.append({"volume_name": vol_name, "chapters": chapters})

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
            "tags": tags,
            "summary_brief": summary_brief,
            "summary": summary,
            "volumes": volumes,
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            logger.warning("qidian chapter %s :: html_list is empty", chapter_id)
            return None
        try:
            ssr_data = self._find_ssr_page_context(html_list[0])
            chapter_info = self._extract_chapter_info(ssr_data)
        except Exception as e:
            logger.warning(
                "qidian chapter %s :: failed to locate ssr_pageContext block: %s",
                chapter_id,
                e,
            )
            return None

        if not chapter_info:
            logger.warning(
                "qidian chapter %s :: ssr_chapterInfo not found.", chapter_id
            )
            return None

        if not self._can_view_chapter(chapter_info):
            logger.warning(
                "qidian chapter %s :: not purchased or inaccessible.", chapter_id
            )
            return None

        duplicated = self._is_duplicated(chapter_info)
        encrypted = self._is_encrypted(chapter_info)

        title = chapter_info.get("chapterName", "Untitled")
        raw_html = chapter_info.get("content", "")
        cid = str(chapter_info.get("chapterId") or chapter_id)
        fkp = chapter_info.get("fkp", "")
        fuid = self._fuid or get_cookie_value(self._state_files, "ywguid")
        author_say = chapter_info.get("authorSay", "").strip()
        update_time = chapter_info.get("updateTime", "")
        update_timestamp = chapter_info.get("updateTimestamp", 0)
        modify_time = chapter_info.get("modifyTime", 0)
        word_count = chapter_info.get("actualWords", 0)
        seq = chapter_info.get("seq")
        volume = chapter_info.get("extra", {}).get("volumeName", "")

        if self._is_vip(chapter_info):
            decryptor = get_decryptor()
            raw_html = decryptor.decrypt_qd(raw_html, cid, fkp, fuid)

        chapter_text = (
            self._parse_font_encrypted(raw_html, chapter_info, cid)
            if encrypted
            else self._parse_normal(raw_html)
        )
        if not chapter_text:
            logger.warning(
                "qidian chapter %s :: content empty after decryption/font-mapping",
                chapter_id,
            )
            return None

        if self._use_truncation and duplicated:
            chapter_text = truncate_half_lines(chapter_text)

        return {
            "id": cid,
            "title": title,
            "content": chapter_text,
            "extra": {
                "site": self.site_name,
                "author_say": author_say,
                "updated_at": update_time,
                "update_timestamp": update_timestamp,
                "modify_time": modify_time,
                "word_count": word_count,
                "duplicated": duplicated,
                "seq": seq,
                "volume": volume,
                "encrypted": encrypted,
            },
        }

    def _parse_normal(self, raw_html: str) -> str:
        """
        Extract structured chapter content from a normal Qidian page.
        """
        parts = raw_html.split("<p>")
        paragraphs = [unescape(p).strip() for p in parts if p.strip()]
        chapter_text = "\n".join(paragraphs)
        if not chapter_text:
            return ""
        return chapter_text

    def _parse_font_encrypted(
        self,
        raw_html: str,
        chapter_info: dict[str, Any],
        cid: str,
    ) -> str:
        """
        Steps:
          1. Decode and save randomFont bytes; download fixedFont via download().
          2. Parse CSS rules and save debug JSON.
          3. Render encrypted paragraphs, then run OCR font-mapping.
          4. Extracts paragraph texts and formats them.
        """
        if not self._decode_font:
            logger.warning(
                "qidian chapter %s :: font decryption skipped "
                "(set `decode_font=True` to enable)",
                cid,
            )
            return ""

        from novel_downloader.infra.network import download

        css_str = chapter_info.get("css")
        random_font_str = chapter_info.get("randomFont")
        rf = json.loads(random_font_str) if isinstance(random_font_str, str) else None
        rf_data = rf.get("data") if rf else None
        fixed_woff2_url = chapter_info.get("fixedFontWoff2")

        if not css_str:
            logger.warning("qidian chapter %s :: css missing or empty", cid)
            return ""
        if not rf_data:
            logger.warning("qidian chapter %s :: randomFont.data missing or empty", cid)
            return ""
        if not fixed_woff2_url:
            logger.warning("qidian chapter %s :: fixedFontWoff2 missing or empty", cid)
            return ""

        debug_dir = self._debug_dir / "font_debug" / cid
        if self._save_font_debug:
            debug_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._rand_path.parent.mkdir(parents=True, exist_ok=True)
            self._rand_path.write_bytes(bytes(rf_data))
        except Exception as e:
            logger.error(
                "qidian chapter %s :: failed to write randomFont.ttf",
                cid,
                exc_info=e,
            )
            return ""

        fixed_path = download(
            url=fixed_woff2_url,
            target_dir=self._fixed_font_dir,
            on_exist="skip",
        )
        if fixed_path is None:
            logger.warning("qidian chapter %s :: failed to download fixedfont", cid)
            return ""

        css_rules = self._parse_css_rules(css_str)
        paragraphs_str, refl_list = self._render_visible_text(raw_html, css_rules)
        if self._save_font_debug:
            (debug_dir / f"{cid}_debug.txt").write_text(
                paragraphs_str, encoding="utf-8"
            )

        # Run OCR + fallback mapping
        char_set = set(paragraphs_str) - {" ", "\n", "\u3000"}
        refl_set = set(refl_list)
        char_set = char_set - refl_set
        if self._save_font_debug:
            (debug_dir / "char_set_debug.txt").write_text(
                f"char_set:\n{char_set}\n\nrefl_set:\n{refl_set}",
                encoding="utf-8",
            )

        mapping_result = self._generate_font_map(
            fixed_font_path=fixed_path,
            random_font_path=self._rand_path,
            char_set=char_set,
            refl_set=refl_set,
            batch_size=self._batch_size,
        )
        if not mapping_result:
            logger.warning(
                "qidian chapter %s :: font mapping returned empty result", cid
            )
            return ""

        if self._save_font_debug:
            (debug_dir / "font_mapping.json").write_text(
                json.dumps(mapping_result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # Reconstruct final readable text
        original_text = self._apply_font_mapping(
            text=paragraphs_str,
            font_map=mapping_result,
        )

        return "\n".join(
            line.strip() for line in original_text.splitlines() if line.strip()
        )

    @staticmethod
    def _find_ssr_page_context(html_str: str) -> dict[str, Any]:
        """
        Extract SSR JSON from <script id="vite-plugin-ssr_pageContext">.
        """
        tree = html.fromstring(html_str)
        script = tree.xpath('//script[@id="vite-plugin-ssr_pageContext"]/text()')
        return json.loads(script[0].strip()) if script else {}

    @staticmethod
    def _extract_chapter_info(ssr_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract the 'chapterInfo' dictionary from the SSR page context.

        This handles nested key access and returns an empty dict if missing.

        :param ssr_data: The full SSR data object from _find_ssr_page_context().
        :return: A dict with chapter metadata such as chapterName, authorSay, etc.
        """
        page_context = ssr_data.get("pageContext", {})
        page_props = page_context.get("pageProps", {})
        page_data = page_props.get("pageData", {})
        chapter_info = page_data.get("chapterInfo", {})
        return chapter_info if isinstance(chapter_info, dict) else {}

    @classmethod
    def _is_vip(cls, chapter_info: dict[str, Any]) -> bool:
        """
        :return: True if VIP, False otherwise.
        """
        vip_flag = chapter_info.get("vipStatus", 0)
        fens_flag = chapter_info.get("fEnS", 0)
        return bool(vip_flag == 1 and fens_flag != 0)

    @classmethod
    def _can_view_chapter(cls, chapter_info: dict[str, Any]) -> bool:
        """
        A chapter is not viewable if it is marked as VIP
        and has not been purchased.

        :return: True if viewable, False otherwise.
        """
        is_buy = chapter_info.get("isBuy", 0)
        vip_status = chapter_info.get("vipStatus", 0)
        return not (vip_status == 1 and is_buy == 0)

    @classmethod
    def _is_duplicated(cls, chapter_info: dict[str, Any]) -> bool:
        """
        Check if chapter is marked as duplicated (eFW = 1).
        """
        efw_flag = chapter_info.get("eFW", 0)
        return bool(efw_flag == 1)

    @classmethod
    def _is_encrypted(cls, chapter_info: dict[str, Any]) -> bool:
        """
        Return True if content is encrypted.

        Chapter Encryption Status (cES):
          * 0: 内容是'明文'
          * 2: 字体加密
        """
        return int(chapter_info.get("cES", 0)) == 2

    def _generate_font_map(
        self,
        fixed_font_path: Path,
        random_font_path: Path,
        char_set: set[str],
        refl_set: set[str],
        batch_size: int = 32,
    ) -> dict[str, str]:
        """
        Build a mapping from scrambled font chars to real chars.

        Uses OCR to decode and generate mapping from a fixed obfuscated font
        and an random obfuscated font. Results are cached in JSON.

        :param fixed_font_path: fixed font file.
        :param random_font_path: random font file.
        :param char_set: Characters to match directly.
        :param refl_set: Characters to match in flipped form.
        :param batch_size: How many chars to OCR per batch.

        :return: { obf_char: real_char, ... }
        """
        font_ocr = get_font_ocr(self._fontocr_cfg)
        if not font_ocr:
            return {}

        mapping_result: dict[str, str] = {}
        fixed_map_file = self._fixed_map_dir / f"{fixed_font_path.stem}.json"
        fixed_map_file.parent.mkdir(parents=True, exist_ok=True)

        # load existing cache
        try:
            with open(fixed_map_file, encoding="utf-8") as f:
                fixed_map = json.load(f)
            cached_chars = set(fixed_map.keys())
            mapping_result.update(
                {ch: fixed_map[ch] for ch in char_set if ch in fixed_map}
            )
            mapping_result.update(
                {ch: fixed_map[ch] for ch in refl_set if ch in fixed_map}
            )
            char_set = char_set - cached_chars
            refl_set = refl_set - cached_chars
        except Exception:
            fixed_map = {}
            cached_chars = set()

        # prepare font renderers and cmap sets
        fixed_chars = font_ocr.extract_font_charset(fixed_font_path)
        random_chars = font_ocr.extract_font_charset(random_font_path)
        fixed_font = font_ocr.load_render_font(fixed_font_path)
        random_font = font_ocr.load_render_font(random_font_path)

        # process normal and reflected sets together
        rendered = []
        for chars, reflect in [(char_set, False), (refl_set, True)]:
            for ch in chars:
                if ch in fixed_chars:
                    font = fixed_font
                elif ch in random_chars:
                    font = random_font
                else:
                    continue
                rendered.append(
                    (ch, font_ocr.render_char_image_array(ch, font, reflect))
                )

        if rendered:
            # query OCR+vec simultaneously
            imgs_to_query = [img for _, img in rendered]
            fused = font_ocr.predict(imgs_to_query, batch_size=batch_size)

            # pick best per char, apply threshold + cache
            for (ch, _), preds in zip(rendered, fused, strict=False):
                if not preds:
                    continue
                real_char, _ = preds
                mapping_result[ch] = real_char
                fixed_map[ch] = real_char

        # persist updated fixed_map
        try:
            with open(fixed_map_file, "w", encoding="utf-8") as f:
                json.dump(fixed_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save fixed map (qidian): %s", e)

        return mapping_result

    @staticmethod
    def _apply_font_mapping(text: str, font_map: dict[str, str]) -> str:
        """
        Replace each character in `text` using `font_map`,
        leaving unmapped characters unchanged.

        :param text: The input string, possibly containing obfuscated font chars.
        :param font_map: A dict mapping obfuscated chars to real chars.
        :return: The de-obfuscated text.
        """
        return "".join(font_map.get(ch, ch) for ch in text)

    @staticmethod
    def _only_tag(selector: str) -> str | None:
        """
        Normalize a selector into just its tag name for ordering.

        Handles forms like 'i', 'em::before', '.p3 i', '.p2 span::after'.

        Returns None if can't extract a tag.
        """
        # If it has spaces, take the rightmost simple selector
        last = selector.strip().split()[-1]
        # Drop ::pseudo
        last = last.split("::", 1)[0]
        # If it's like 'span[attr=..]' keep 'span'
        last = last.split("[", 1)[0]
        # If it starts with '.', it's not a tag
        if not last or last.startswith("."):
            return None
        return last

    @staticmethod
    def _parse_decls(block: str) -> list[tuple[str, str]]:
        """
        Parse 'name:value;...' inside a block. Tolerates quotes and attr().
        """
        parts = [d.strip() for d in block.split(";") if d.strip()]
        decls = []
        for p in parts:
            if ":" in p:
                name, val = p.split(":", 1)
                decls.append((name.strip().lower(), val.strip()))
        return decls

    @classmethod
    def _parse_css_rules(cls, css_str: str) -> Rules:
        """
        Produces normalized Rules with:
          * orders: list[str] of tag names sorted by numeric 'order'
          * sy: '.sy-*' class rules
          * p_rules: '.p* <tag>' rules, indexed by p-class then tag
        """
        rules: Rules = {"orders": [], "sy": {}, "p_rules": {}}
        order_pairs: list[tuple[str, int]] = []

        pos = 0
        while True:
            b1 = css_str.find("{", pos)
            if b1 == -1:
                break
            selector = css_str[pos:b1].strip().lower()
            b2 = css_str.find("}", b1 + 1)
            if b2 == -1:
                break
            block = css_str[b1 + 1 : b2]
            pos = b2 + 1

            decls = cls._parse_decls(block)
            new_rule: Rule = {}
            order_val: int | None = None

            for name, value in decls:
                v = value.strip()
                if name == "font-size" and v == "0":
                    new_rule[
                        "delete_first" if "::first-letter" in selector else "delete_all"
                    ] = True
                elif name == "transform" and "scalex(-1" in v.replace(" ", "").lower():
                    new_rule["transform_flip_x"] = True
                elif name == "order":
                    with suppress(ValueError):
                        order_val = int(v)
                elif name == "content":
                    if "::after" in selector:
                        if v.lower().startswith("attr("):
                            new_rule["append_end_attr"] = v[5:-1].strip()
                        else:
                            new_rule["append_end_char"] = v.strip().strip("\"'")
                    elif "::before" in selector:
                        if v.lower().startswith("attr("):
                            new_rule["append_start_attr"] = v[5:-1].strip()
                        else:
                            new_rule["append_start_char"] = v.strip().strip("\"'")

            if selector.startswith(".sy-"):
                key = selector.lstrip(".")
                rules["sy"][key] = {**rules["sy"].get(key, {}), **new_rule}
            elif selector.startswith(".p") and " " in selector:
                p_cls, right = selector.split(" ", 1)
                tag = cls._only_tag(right)
                if tag:
                    p_cls = p_cls.lstrip(".")
                    rules["p_rules"].setdefault(p_cls, {})
                    rules["p_rules"][p_cls][tag] = {
                        **rules["p_rules"][p_cls].get(tag, {}),
                        **new_rule,
                    }

            if order_val is not None:
                tag = cls._only_tag(selector)
                if tag:
                    order_pairs.append((tag, order_val))

        rules["orders"] = [t for t, _ in sorted(order_pairs, key=lambda x: x[1])]
        return rules

    @staticmethod
    def _render_visible_text(html_str: str, rules: Rules) -> tuple[str, list[str]]:
        """
        Renderer the HTML using pre-parsed Rules.
        """
        tree = html.fromstring(html_str)
        paragraphs_out: list[str] = []
        refl_list: list[str] = []
        orders = rules.get("orders") or []
        p_rules = rules.get("p_rules") or {}
        sy_rules = rules.get("sy") or {}

        def _class_list(el: html.HtmlElement) -> list[str]:
            cls = el.get("class")
            return cls.split() if cls else []

        def _apply_rule(el: html.HtmlElement, rule: Rule) -> str:
            if rule.get("delete_all"):
                return ""

            parts: list[str] = []
            if "append_start_char" in rule:
                parts.append(rule["append_start_char"])
            if "append_start_attr" in rule:
                parts.append(el.get(rule["append_start_attr"], ""))

            text = el.text or ""
            if rule.get("delete_first") and text:
                text = text[1:]
            parts.append(text)

            if "append_end_char" in rule:
                parts.append(rule["append_end_char"])
            if "append_end_attr" in rule:
                parts.append(el.get(rule["append_end_attr"], ""))

            s = "".join(parts)

            if rule.get("transform_flip_x") and s:
                refl_list.append(s)

            return s

        for p in tree.findall(".//p"):
            p_classes = _class_list(p)
            p_key = next((c for c in p_classes if c.startswith("p")), None)
            has_ordered_rules = p_key in p_rules

            buf_parts: list[str] = []

            if p.text and not has_ordered_rules:
                buf_parts.append(p.text)

            ordered_cache: dict[str, list[str]] = {}

            for child in p:
                tag = str(child.tag)

                # Handle inline <y class="sy-*"> spans
                if tag == "y" and not has_ordered_rules:
                    y_cls = next(
                        (c for c in _class_list(child) if c.startswith("sy-")), None
                    )
                    if y_cls and y_cls in sy_rules:
                        buf_parts.append(_apply_rule(child, sy_rules[y_cls]))
                    else:
                        buf_parts.append(child.text or "")
                    if child.tail:
                        buf_parts.append(child.tail)
                    continue

                # Handle ordered paragraphs: only cache tags that appear in `orders`
                if p_key and has_ordered_rules and tag in orders:
                    rule = p_rules[p_key].get(tag, {})
                    ordered_cache.setdefault(tag, []).append(_apply_rule(child, rule))
                    continue

                # Non-ordered, non-<y> nodes: include text + tails as-is
                if not has_ordered_rules:
                    buf_parts.append(child.text or "")
                    if child.tail:
                        buf_parts.append(child.tail)

            # If ordered, flush in global orders with all duplicates preserved
            if has_ordered_rules:
                for tag in orders:
                    if tag in ordered_cache:
                        buf_parts.extend(ordered_cache[tag])

            para = "".join(buf_parts)
            if para:
                paragraphs_out.append(para)

        return "\n".join(paragraphs_out), refl_list
