import json

from novel_downloader.infra.persistence.state import StateManager


def test_load_nonexistent_file(tmp_path):
    """When file does not exist, StateManager should load empty state."""
    f = tmp_path / "state.json"
    mgr = StateManager(f)

    assert mgr.get_language() == "zh_CN"  # default
    assert f.exists() is False  # no auto-create on load


def test_set_and_get_language(tmp_path):
    """Setting language should persist to file."""
    f = tmp_path / "state.json"
    mgr = StateManager(f)

    mgr.set_language("en_US")
    assert mgr.get_language() == "en_US"

    # Ensure file was actually written
    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["lang"] == "en_US"


def test_load_existing_state(tmp_path):
    """Loading a pre-existing JSON file should populate state."""
    f = tmp_path / "state.json"
    f.write_text(json.dumps({"lang": "ja_JP"}), encoding="utf-8")

    mgr = StateManager(f)
    assert mgr.get_language() == "ja_JP"


def test_load_invalid_json(tmp_path):
    """Invalid JSON should be treated as empty state."""
    f = tmp_path / "state.json"
    f.write_text("{not a json", encoding="utf-8")

    mgr = StateManager(f)
    assert mgr.get_language() == "zh_CN"  # fallback to default
    # Writing should overwrite invalid file
    mgr.set_language("ko_KR")
    assert json.loads(f.read_text(encoding="utf-8"))["lang"] == "ko_KR"


def test_save_creates_parent_dirs(tmp_path):
    """Saving should auto-create parent directories."""
    nested_dir = tmp_path / "a/b/c"
    f = nested_dir / "state.json"

    mgr = StateManager(f)
    mgr.set_language("fr_FR")

    assert f.exists()
    data = json.loads(f.read_text(encoding="utf-8"))
    assert data["lang"] == "fr_FR"
