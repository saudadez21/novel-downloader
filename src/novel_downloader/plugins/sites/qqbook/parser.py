#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.parser
--------------------------------------------

"""

from __future__ import annotations

import json
import logging
import re
from contextlib import suppress
from pathlib import Path
from typing import Any, TypedDict

from lxml import html

from novel_downloader.infra.fontocr import get_font_ocr
from novel_downloader.infra.jsbridge import get_decryptor
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
class QqbookParser(BaseParser):
    """
    Parser for QQ 阅读 site.
    """

    site_name: str = "qqbook"

    _NUXT_BLOCK_RE = re.compile(
        r"window\.__NUXT__\s*=\s*([\s\S]*?);?\s*<\/script>",
        re.S,
    )

    def __init__(self, config: ParserConfig):
        """
        Initialize the QqbookParser with the given configuration.
        """
        super().__init__(config)

        self._rand_path = self._base_cache_dir / "qqbook" / "randomFont.ttf"
        self._fixed_font_dir = self._base_cache_dir / "qqbook" / "fixed_fonts"
        self._fixed_map_dir = self._base_cache_dir / "qqbook" / "fixed_font_map"
        self._debug_dir = Path.cwd() / "debug" / "qqbook"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        Order: [info, catalog]

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_dict = json.loads(html_list[1])

        book_name = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        ) or self._first_str(
            info_tree.xpath('//h1[contains(@class, "book-title")]/text()')
        )
        author = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:author"]/@content')
        ) or self._first_str(
            info_tree.xpath(
                '//div[contains(@class,"book-meta")]//a[contains(@class,"author")]/text()'
            ),
            replaces=[(" 著", ""), ("著", "")],
        )
        cover_url = self._first_str(
            info_tree.xpath('//meta[@property="og:image"]/@content')
        ) or self._first_str(
            info_tree.xpath('//div[contains(@class,"book-cover")]//img/@src')
        )
        update_time = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        ) or self._first_str(
            info_tree.xpath('//div[contains(@class,"update-time")]/text()'),
            replaces=[("更新时间：", "")],
        )
        serial_status = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:status"]/@content')
        )
        # tags
        tags = [
            t.strip()
            for t in info_tree.xpath(
                '//div[contains(@class,"book-tags")]//a[contains(@class,"tag")]/text()'
            )
            if t.strip()
        ]
        # summary
        summary_raw = "\n".join(
            info_tree.xpath('//div[contains(@class,"book-intro")]//text()')
        )
        summary = (
            self._norm_space(summary_raw)
            if summary_raw
            else self._first_str(
                info_tree.xpath('//meta[@property="og:description"]/@content')
            )
        )

        # book_id for chapter URLs
        read_url = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:read_url"]/@content')
        ) or self._first_str(info_tree.xpath('//meta[@property="og:url"]/@content'))
        book_id = ""
        if read_url:
            book_id = read_url.rstrip("/").split("/")[-1]

        # Chapters from the book_list
        data = catalog_dict.get("data") or []
        chapters: list[ChapterInfoDict] = []
        for item in data:
            cid = str(item.get("cid"))
            title = str(item.get("chapterName", "")).strip()
            accessible = bool(item.get("free") or item.get("purchased"))
            chap: ChapterInfoDict = {
                "title": title,
                "chapterId": cid,
                "url": f"/book-read/{book_id}/{cid}" if book_id and cid else "",
                "accessible": accessible,
            }
            chapters.append(chap)

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "tags": tags,
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
            logger.warning("QQbook chapter %s :: html_list is empty", chapter_id)
            return None
        try:
            nuxt_block = self._find_nuxt_block(html_list[0])
            data_list = nuxt_block.get("data")
            if not data_list:
                return None
            data_block = data_list[0]
        except Exception as e:
            logger.warning(
                "QQbook chapter %s :: failed to locate Nuxt block: %s",
                chapter_id,
                e,
            )
            return None

        curr_content = data_block.get("currentContent") or {}
        if not curr_content:
            logger.warning(
                "QQbook chapter %s :: currentContent missing or empty", chapter_id
            )
            return None

        content = curr_content.get("content", "")
        if not content:
            logger.warning(
                "QQbook chapter %s :: raw 'content' missing or empty", chapter_id
            )
            return None

        title = data_block.get("chapterTitle", "Untitled")
        cid = str(data_block.get("cid") or chapter_id)
        bk_cfg = data_block.get("fkConfig") or {}
        encrypt = curr_content.get("encrypt", False)
        font_encrypt = bool(curr_content.get("fontEncrypt"))
        font_resp = curr_content.get("fontResponse") or {}

        update_time = curr_content.get("updateTime") or ""
        word_count = curr_content.get("totalWords") or ""

        logger.debug(
            "QQbook chapter %s :: meta title=%r encrypt=%s font_encrypt=%s",
            chapter_id,
            title,
            encrypt,
            font_encrypt,
        )

        if encrypt:
            try:
                content = self._parse_encrypted(content=content, cid=cid, bk_cfg=bk_cfg)
            except Exception as e:
                logger.warning(
                    "QQbook chapter %s :: encrypted content decryption failed: %s",
                    chapter_id,
                    e,
                )
                return None

        if font_encrypt:
            content = self._parse_font_encrypted(
                content=content,
                font_resp=font_resp,
                cid=cid,
            )

        if not content:
            logger.warning(
                "QQbook chapter %s :: content empty after decryption/font-mapping",
                chapter_id,
            )
            return None

        return {
            "id": cid,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "updated_at": update_time,
                "word_count": word_count,
                "encrypt": encrypt,
                "font_encrypt": font_encrypt,
            },
        }

    def _parse_encrypted(
        self,
        content: str,
        cid: str,
        bk_cfg: dict[str, Any],
    ) -> str:
        decryptor = get_decryptor()
        fkp = bk_cfg.get("fkp", "")
        fuid = bk_cfg.get("fuid", "")
        return decryptor.decrypt_qq(
            ciphertext=content,
            chapter_id=cid,
            fkp=fkp,
            fuid=fuid,
        )

    def _parse_font_encrypted(
        self,
        content: str,
        font_resp: dict[str, Any],
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
                "QQbook chapter %s :: font decryption skipped "
                "(set `decode_font=True` to enable)",
                cid,
            )
            return ""

        from novel_downloader.infra.network import download

        css_str = font_resp.get("css")
        random_font = font_resp.get("randomFont") or {}
        rf_data = random_font.get("data") if isinstance(random_font, dict) else None
        fixed_woff2_url = font_resp.get("fixedFontWoff2")

        if not css_str:
            logger.warning("QQbook chapter %s :: css missing or empty", cid)
            return ""
        if not rf_data:
            logger.warning("QQbook chapter %s :: randomFont.data missing or empty", cid)
            return ""
        if not fixed_woff2_url:
            logger.warning("QQbook chapter %s :: fixedFontWoff2 missing or empty", cid)
            return ""

        debug_dir = self._debug_dir / "font_debug" / cid
        if self._save_font_debug:
            debug_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._rand_path.parent.mkdir(parents=True, exist_ok=True)
            self._rand_path.write_bytes(bytes(rf_data))
        except Exception as e:
            logger.error(
                "QQbook chapter %s :: failed to write randomFont.ttf",
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
            logger.warning("QQbook chapter %s :: failed to download fixedfont.", cid)
            return ""

        css_rules = self._parse_css_rules(css_str)
        paragraphs_str, refl_list = self._render_visible_text(content, css_rules)
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
                "QQbook chapter %s :: font mapping returned empty result.", cid
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

        final_paragraphs_str = "\n".join(
            line.strip() for line in original_text.splitlines() if line.strip()
        )

        return final_paragraphs_str

    @classmethod
    def _find_nuxt_block(cls, html_str: str) -> dict[str, Any]:
        m = cls._NUXT_BLOCK_RE.search(html_str)
        if not m:
            return {}
        js_code = m.group(1).rstrip()  # RHS only
        decryptor = get_decryptor()
        return decryptor.eval_to_json(js_code)

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
        :param cache_dir: Directory to save/load cached results.
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
            logger.error("Failed to save fixed map (QQbook): %s", e)

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
