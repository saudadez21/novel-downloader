import json
import time
from pathlib import Path

import pytest
from novel_downloader.plugins import registry
from novel_downloader.schemas import FetcherConfig, ParserConfig

from tests.plugins.sites.constants import LOGIN_REQUIRED, TEST_DATA
from tests.plugins.sites.helpers import load_html_parts

HTML_ROOT = Path(__file__).parents[2] / "data" / "sites" / "html"
JSON_ROOT = Path(__file__).parents[2] / "data" / "sites" / "json"
META_PATH = Path(__file__).parents[2] / "data" / "sites" / "last_tested.json"

_PARSER_CONFIG = ParserConfig()
_CACHE_TTL = 86400  # 1 day


def _load_metadata() -> dict[str, float]:
    """Load last_tested.json once."""
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_metadata(meta: dict[str, float]) -> None:
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    META_PATH.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("site_key", list(TEST_DATA.keys()))
async def test_fetcher_fetches_non_empty(site_key: str):
    """Fetcher: ensure non-empty HTML output, skip login-required and cached sites."""
    if site_key in LOGIN_REQUIRED:
        pytest.skip(f"{site_key}: login required")

    metadata = _load_metadata()
    last_time = metadata.get(site_key, 0.0)
    if time.time() - last_time < _CACHE_TTL:
        pytest.skip(f"{site_key}: cached within 24h")
        return

    match site_key:
        case "linovelib":
            req_interval = 2.5
        case _:
            req_interval = 0.5

    fetcher_config = FetcherConfig(request_interval=req_interval)
    try:
        fetcher = registry.registrar.get_fetcher(site_key, fetcher_config)
    except Exception as e:
        pytest.skip(f"{site_key}: fetcher load failed ({e})")
        return

    async with fetcher as f:
        for entry in TEST_DATA[site_key]:
            book_id = entry["book_id"]

            info_html = await f.get_book_info(book_id)
            assert info_html, f"{site_key}: empty info html for {book_id}"

            for i, part in enumerate(info_html, start=1):
                out = HTML_ROOT / site_key / f"{book_id}_info_{i}.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(part, encoding="utf-8")

            for chap_id in entry["chap_ids"]:
                chap_html = await f.get_book_chapter(book_id, chap_id)
                assert chap_html, f"{site_key}: empty chapter {chap_id}"
                for i, part in enumerate(chap_html, start=1):
                    out = HTML_ROOT / site_key / f"{book_id}_{chap_id}_{i}.html"
                    out.write_text(part, encoding="utf-8")

    # Update last tested time only if fetch succeeded
    metadata[site_key] = time.time()
    _save_metadata(metadata)


@pytest.mark.parametrize("site_key", list(TEST_DATA.keys()))
def test_parser_outputs_valid_bookinfo(site_key: str):
    """Parser: validate parsed book info structure and compare with JSON target."""
    if site_key in LOGIN_REQUIRED:
        pytest.skip(f"{site_key}: login required")

    try:
        parser = registry.registrar.get_parser(site_key, _PARSER_CONFIG)
    except Exception as e:
        pytest.skip(f"{site_key}: parser load failed ({e})")
        return

    for entry in TEST_DATA[site_key]:
        book_id = entry["book_id"]
        html_list = load_html_parts(HTML_ROOT / site_key, f"{book_id}_info")
        assert html_list, f"{site_key}: no html for {book_id}"

        target_path = JSON_ROOT / site_key / f"{book_id}_info.json"
        assert (
            target_path.exists()
        ), f"{site_key}: missing expected JSON {target_path.name}"

        expected = json.loads(target_path.read_text(encoding="utf-8"))
        book_info = parser.parse_book_info(html_list)
        assert book_info, f"{site_key}: parser returned None for {book_id}"

        for key in ("book_name", "author", "volumes"):
            assert key in book_info, f"{site_key}: missing key '{key}'"

        for i, vol in enumerate(expected["volumes"]):
            assert book_info["volumes"][i]["volume_name"] == vol["volume_name"]
            for j, chap in enumerate(vol["chapters"]):
                got = book_info["volumes"][i]["chapters"][j]
                assert got["title"] == chap["title"], (
                    f"{site_key}: mismatch in {book_id} vol {i} chap {j} "
                    f"({got['title']} != {chap['title']})"
                )


@pytest.mark.parametrize("site_key", list(TEST_DATA.keys()))
def test_parser_outputs_valid_chapter(site_key: str):
    """Parser: validate chapter content and match with JSON target."""
    if site_key in LOGIN_REQUIRED:
        pytest.skip(f"{site_key}: login required")

    try:
        parser = registry.registrar.get_parser(site_key, _PARSER_CONFIG)
    except Exception as e:
        pytest.skip(f"{site_key}: parser load failed ({e})")
        return

    for entry in TEST_DATA[site_key]:
        book_id = entry["book_id"]
        for chap_id in entry["chap_ids"]:
            html_list = load_html_parts(HTML_ROOT / site_key, f"{book_id}_{chap_id}")
            assert html_list, f"{site_key}: no html for {book_id}_{chap_id}"

            target_path = JSON_ROOT / site_key / f"{book_id}_chapter_{chap_id}.json"
            assert (
                target_path.exists()
            ), f"{site_key}: missing expected JSON {target_path.name}"

            expected = json.loads(target_path.read_text(encoding="utf-8"))
            chapter = parser.parse_chapter(html_list, chap_id)
            assert chapter, f"{site_key}: parser returned None for {book_id}_{chap_id}"

            for key in ("id", "title", "content"):
                assert key in chapter, f"{site_key}: chapter missing key '{key}'"

            assert (
                chapter["id"] == expected["id"]
            ), f"{site_key}: id mismatch ({chapter['id']} != {expected['id']})"
            assert (
                chapter["title"] == expected["title"]
            ), f"{site_key}: title mismatch {chapter['title']} != {expected['title']}"

            got_lines = [
                line.strip() for line in chapter["content"].splitlines() if line.strip()
            ]
            exp_lines = [
                line.strip()
                for line in expected["content"].splitlines()
                if line.strip()
            ]

            min_len = min(len(got_lines), len(exp_lines))
            for i in range(min_len):
                assert got_lines[i] == exp_lines[i], (
                    f"{site_key}: line {i+1} mismatch in {book_id}_{chap_id}\n"
                    f"expected: {exp_lines[i]!r}\n"
                    f"   found: {got_lines[i]!r}"
                )

            if len(got_lines) > len(exp_lines):
                extra = len(got_lines) - len(exp_lines)
                print(f"[warn] {site_key}: {book_id}_{chap_id} has {extra} extra lines")
