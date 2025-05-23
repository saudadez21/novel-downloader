#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.diff_display
----------------------------------------------

Generate inline character-level diff between two strings with visual markers.
"""

import difflib
import unicodedata


def _char_width_space(
    c: str, normal_char: str = " ", asian_char: str = "\u3000"
) -> str:
    """
    Return a placeholder space character matching the width of `c`.

    Fullwidth (F) or Wide (W) characters map to `asian_char`, else `normal_char`.

    :param c:           A single character.
    :param normal_char: Replacement for narrow chars (default U+0020).
    :param asian_char:  Replacement for wide chars (default U+3000).
    :return:            The appropriate space character.
    """
    return asian_char if unicodedata.east_asian_width(c) in ("F", "W") else normal_char


def diff_inline_display(old_str: str, new_str: str) -> str:
    """
    Show inline diff between two strings,
    marking deletions with '^' and insertions with '^'.

    :param old_str: Original string (prefixed '-' will be trimmed).
    :param new_str: Modified string (prefixed '+' will be trimmed).
    :return:        A multiline diff display with aligned markers.
    """
    space_1 = " "
    space_2 = "\u3000"
    mark_1 = "^"
    mark_2 = "\ufe3f"  # '人' / '\ufe3f' / '宀' / '立' / '八'

    # Clean leading +/- if present
    s1 = old_str.lstrip("-").strip()
    s2 = new_str.lstrip("+").strip()

    sm = difflib.SequenceMatcher(None, s1, s2)
    marker_s1 = ""
    marker_s2 = ""

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            s1_seg = s1[i1:i2]
            s2_seg = s2[j1:j2]
            marker_s1 += "".join(_char_width_space(c, space_1, space_2) for c in s1_seg)
            marker_s2 += "".join(_char_width_space(c, space_1, space_2) for c in s2_seg)
        elif tag == "delete":
            seg = s1[i1:i2]
            marker_s1 += "".join(_char_width_space(c, mark_1, mark_2) for c in seg)
        elif tag == "insert":
            seg = s2[j1:j2]
            marker_s2 += "".join(_char_width_space(c, mark_1, mark_2) for c in seg)
        elif tag == "replace":
            s1_seg = s1[i1:i2]
            s2_seg = s2[j1:j2]
            marker_s1 += "".join(_char_width_space(c, mark_1, mark_2) for c in s1_seg)
            marker_s2 += "".join(_char_width_space(c, mark_1, mark_2) for c in s2_seg)
    output_str = f"-{s1}\n {marker_s1}\n+{s2}\n {marker_s2}"
    return output_str


__all__ = [
    "diff_inline_display",
]
