#!/usr/bin/env python3
import json
import pathlib
import re

import pytest
from novel_downloader.plugins.utils.js_eval import get_evaluator

DATA_BASE = pathlib.Path(__file__).resolve().parents[2] / "data" / "plugins" / "qqbook"

# All directories: case_*
CASE_DIRS = sorted([p for p in DATA_BASE.glob("case_*") if p.is_dir()])

_NUXT_BLOCK_RE = re.compile(
    r"window\.__NUXT__\s*=\s*([\s\S]*?);?\s*</script>",
    re.S,
)


def extract_js_rhs(html: str) -> str | None:
    """
    Extract only the RHS of window.__NUXT__ = ... from the test HTML.
    """
    m = _NUXT_BLOCK_RE.search(html)
    if not m:
        return None
    return m.group(1).rstrip()


@pytest.mark.skipif(
    not DATA_BASE.exists() or not CASE_DIRS,
    reason="No QQ book test data found under tests/data/plugins/qqbook/",
)
@pytest.mark.parametrize("case_dir", CASE_DIRS)
def test_qqbook_js_eval(case_dir: pathlib.Path):
    """
    Test whether js_eval can parse QQBook's window.__NUXT__ JS block
    """
    html_path = case_dir / "input.html"
    expected_path = case_dir / "expected.json"

    html = html_path.read_text(encoding="utf-8")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    js_code = extract_js_rhs(html)
    assert js_code, f"No __NUXT__ block found in: {case_dir}"

    evaluator = get_evaluator()

    # Direct Python parser
    try:
        py_result = evaluator._eval_direct(js_code.strip())
    except Exception:
        py_result = None

    # Node-only evaluation
    node_result = evaluator._eval_node(js_code)

    # Production evaluator (fast-path + fallback)
    mixed_result = evaluator.eval(js_code)

    # At least one success
    assert any(
        r is not None for r in (py_result, mixed_result, node_result)
    ), f"All eval paths failed for case: {case_dir}"

    # Compare all valid results to expected.json
    if py_result is not None:
        assert py_result == expected, "Python fast-path mismatch"

    if mixed_result is not None:
        assert mixed_result == expected, "eval_to_json mismatch"

    if node_result is not None:
        assert node_result == expected, "Node-only mismatch"
