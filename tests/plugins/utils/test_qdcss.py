#!/usr/bin/env python3

import json
import pathlib

import pytest

from novel_downloader.plugins.utils.yuewen.qdcss import apply_css_text_rules

DATA_BASE = pathlib.Path(__file__).resolve().parents[2] / "data" / "plugins" / "yuewen"

# All case directories: case_qd_*
CASE_DIRS = sorted([p for p in DATA_BASE.glob("case_qd_*") if p.is_dir()])


def pytest_generate_tests(metafunc):
    """Dynamically parametrize test if cases exist."""
    if "case_dir" in metafunc.fixturenames:
        if not DATA_BASE.exists():
            # no data folder
            metafunc.parametrize("case_dir", [])
            return

        if not CASE_DIRS:
            # no case found
            metafunc.parametrize("case_dir", [])
            return

        metafunc.parametrize("case_dir", CASE_DIRS)


@pytest.mark.skipif(
    not DATA_BASE.exists() or not CASE_DIRS,
    reason="No Yuewen test data found under tests/data/plugins/yuewen/",
)
def test_apply_css_text_rules(case_dir: pathlib.Path):
    """Test a single Yuewen case: HTML + CSS -> expected text & refl list."""
    html_path = case_dir / "input.html"
    css_path = case_dir / "input.css"
    expected_text_path = case_dir / "expected.txt"
    expected_refl_path = case_dir / "expected_refl.json"

    # --- Validate required files ---
    for p in (html_path, css_path, expected_text_path, expected_refl_path):
        assert p.exists(), f"Missing required file: {p}"

    # --- Load test data ---
    html_str = html_path.read_text(encoding="utf-8")
    css_str = css_path.read_text(encoding="utf-8")
    expected_text = expected_text_path.read_text(encoding="utf-8").strip()
    expected_refl = json.loads(expected_refl_path.read_text(encoding="utf-8"))

    # --- Run and compare ---
    out_text, refl_list = apply_css_text_rules(html_str, css_str)

    assert out_text.strip() == expected_text
    assert refl_list == expected_refl
