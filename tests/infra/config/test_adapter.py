import pytest

from novel_downloader.infra.config.adapter import ConfigAdapter
from novel_downloader.schemas import (
    BookConfig,
    ClientConfig,
    ExporterConfig,
    FetcherConfig,
    OCRConfig,
    ParserConfig,
    ProcessorConfig,
)


@pytest.fixture
def sample_config(tmp_path) -> dict:
    """Construct a representative configuration mapping for tests."""
    return {
        "general": {
            "cache_dir": str(tmp_path / "cache"),
            "raw_data_dir": str(tmp_path / "raw"),
            "output_dir": str(tmp_path / "downloads"),
            "request_interval": 1.0,
            "workers": 8,
            "max_connections": 20,
            "max_rps": 500.0,
            "retry_times": 5,
            "backoff_factor": 3.0,
            "timeout": 10.0,
            "storage_batch_size": 2,
            "cache_chapter": False,
            "cache_book_info": False,
            "fetch_inaccessible": True,
            "login_required": False,
            "locale_style": "traditional",
            "backend": "httpx",
            "impersonate": "general-imp",
            "verify_ssl": False,
            "http2": False,
            "proxy": "http://general-proxy",
            "proxy_user": "g-user",
            "proxy_pass": "g-pass",
            "trust_env": True,
            "user_agent": "general-UA",
            "headers": {"X-Header": "general"},
            "parser": {
                "enable_ocr": False,
                "batch_size": 16,
                "remove_watermark": False,
                "cut_mode": "none",
                "model_name": "general-model",
                "input_shape": [3, 32, 320],
                "precision": "fp32",
                "cpu_threads": 4,
                "device": "cpu",
            },
            "debug": {
                "save_html": True,
                "log_level": "DEBUG",
                "log_dir": str(tmp_path / "logs"),
            },
            "output": {
                "render_missing_chapter": False,
                "append_timestamp": False,
                "filename_template": "{title}",
                "include_picture": False,
                "formats": ["epub"],
            },
            "processors": [
                {"name": "normalize", "overwrite": False, "foo": 1},
                {"name": "cleanup", "overwrite": True},
            ],
        },
        "sites": {
            "example": {
                "request_interval": 2.0,
                "timeout": 5.0,
                "max_rps": 800.0,
                "user_agent": "site-UA",
                "verify_ssl": True,
                "cache_book_info": True,
                "cache_chapter": True,
                # login info
                "username": " user ",
                "password": "",
                "cookies": " cookie=1 ",
                "login_required": True,
                "parser": {
                    "enable_ocr": True,
                    "batch_size": 8,
                    "remove_watermark": True,
                    "cut_mode": "line",
                    "use_truncation": False,
                    "model_name": "site-model",
                    "precision": "int8",
                },
                "output": {
                    "render_missing_chapter": True,
                    "append_timestamp": True,
                    "filename_template": "{title}-{site}",
                    "include_picture": True,
                    "split_mode": "volume",
                    "formats": ["epub", "mobi"],
                },
                "processors": [
                    {"name": "site-only", "overwrite": False, "bar": 2},
                ],
                "book_ids": [
                    "123",
                    456,
                    {
                        "book_id": "789",
                        "start_id": 1,
                        "end_id": 2,
                        "ignore_ids": [3, 4],
                    },
                ],
            },
            "no_site_specific": {
                # use general
            },
        },
        "plugins": {
            "enable_local_plugins": True,
            "local_plugins_path": str(tmp_path / "plugins"),
            "override_builtins": True,
        },
    }


@pytest.fixture
def adapter(sample_config) -> ConfigAdapter:
    return ConfigAdapter(sample_config)


def test_get_config_returns_shallow_copy(adapter, sample_config):
    cfg = adapter.get_config()
    assert cfg == sample_config
    assert cfg is not sample_config


# ---------------------------------------------------------------------------
# get_fetcher_config
# ---------------------------------------------------------------------------


def test_get_fetcher_config_site_overrides_general(adapter, sample_config):
    fetcher = adapter.get_fetcher_config("example")
    assert isinstance(fetcher, FetcherConfig)

    assert fetcher.request_interval == 2.0  # site
    assert fetcher.timeout == 5.0  # site
    assert fetcher.max_rps == 800.0  # site

    assert fetcher.retry_times == 5
    assert fetcher.max_connections == 20
    assert fetcher.backend == "httpx"
    assert fetcher.locale_style == "traditional"

    assert fetcher.cache_dir == sample_config["general"]["cache_dir"]

    assert fetcher.verify_ssl is True
    assert fetcher.http2 is False
    assert fetcher.user_agent == "site-UA"


def test_get_fetcher_config_defaults_when_missing(tmp_path):
    adapter = ConfigAdapter({"general": {}, "sites": {"s": {}}})
    fetcher = adapter.get_fetcher_config("s")

    assert fetcher.request_interval == 0.5
    assert fetcher.retry_times == 3
    assert fetcher.backoff_factor == 2.0
    assert fetcher.cache_dir == "./novel_cache"
    assert fetcher.backend == "aiohttp"
    assert fetcher.locale_style == "simplified"


# ---------------------------------------------------------------------------
# get_parser_config
# ---------------------------------------------------------------------------


def test_get_parser_config_merging_and_ocr(adapter, sample_config):
    parser_cfg = adapter.get_parser_config("example")
    assert isinstance(parser_cfg, ParserConfig)

    general_cache_dir = sample_config["general"]["cache_dir"]
    assert parser_cfg.cache_dir == general_cache_dir

    assert parser_cfg.use_truncation is False

    assert parser_cfg.enable_ocr is True
    assert parser_cfg.batch_size == 8
    assert parser_cfg.remove_watermark is True
    assert parser_cfg.cut_mode == "line"

    ocr_cfg = parser_cfg.ocr_cfg
    assert isinstance(ocr_cfg, OCRConfig)
    assert ocr_cfg.model_name == "site-model"
    assert ocr_cfg.precision == "int8"
    assert ocr_cfg.cpu_threads == 4
    assert ocr_cfg.input_shape == (3, 32, 320)


# ---------------------------------------------------------------------------
# get_client_config
# ---------------------------------------------------------------------------


def test_get_client_config_merging(adapter, sample_config):
    client_cfg = adapter.get_client_config("example")
    assert isinstance(client_cfg, ClientConfig)

    assert client_cfg.request_interval == 2.0
    assert client_cfg.retry_times == 5

    assert client_cfg.raw_data_dir == sample_config["general"]["raw_data_dir"]
    assert client_cfg.cache_dir == sample_config["general"]["cache_dir"]
    assert client_cfg.output_dir == sample_config["general"]["output_dir"]
    assert client_cfg.workers == 8

    assert client_cfg.save_html is True

    assert client_cfg.cache_book_info is True
    assert client_cfg.cache_chapter is True
    assert client_cfg.fetch_inaccessible is True
    assert client_cfg.storage_batch_size == 2

    assert isinstance(client_cfg.fetcher_cfg, FetcherConfig)
    assert isinstance(client_cfg.parser_cfg, ParserConfig)


# ---------------------------------------------------------------------------
# get_exporter_config
# ---------------------------------------------------------------------------


def test_get_exporter_config_merging(adapter):
    exporter_cfg = adapter.get_exporter_config("example")
    assert isinstance(exporter_cfg, ExporterConfig)

    # out = {**general.output, **site.output}
    assert exporter_cfg.render_missing_chapter is True
    assert exporter_cfg.append_timestamp is True
    assert exporter_cfg.filename_template == "{title}-{site}"
    assert exporter_cfg.include_picture is True

    assert exporter_cfg.split_mode == "volume"


# ---------------------------------------------------------------------------
# login-related
# ---------------------------------------------------------------------------


def test_get_login_config_trims_and_filters(adapter):
    login_cfg = adapter.get_login_config("example")
    # password is empty
    assert login_cfg == {
        "username": "user",
        "cookies": "cookie=1",
    }


def test_get_login_required_site_overrides_general(adapter):
    # general.login_required=False, site.login_required=True
    assert adapter.get_login_required("example") is True
    assert adapter.get_login_required("no_site_specific") is False


# ---------------------------------------------------------------------------
# export formats
# ---------------------------------------------------------------------------


def test_get_export_fmt_site_overrides_general(adapter):
    fmts = adapter.get_export_fmt("example")
    assert fmts == ["epub", "mobi"]

    fmts2 = adapter.get_export_fmt("no_site_specific")
    assert fmts2 == ["epub"]


# ---------------------------------------------------------------------------
# plugins config
# ---------------------------------------------------------------------------


def test_get_plugins_config(adapter, sample_config):
    plugins_cfg = adapter.get_plugins_config()
    assert plugins_cfg == {
        "enable_local_plugins": True,
        "local_plugins_path": sample_config["plugins"]["local_plugins_path"],
        "override_builtins": True,
    }


def test_get_plugins_config_defaults_when_missing():
    adapter = ConfigAdapter({})
    plugins_cfg = adapter.get_plugins_config()
    assert plugins_cfg == {
        "enable_local_plugins": False,
        "local_plugins_path": "",
        "override_builtins": False,
    }


# ---------------------------------------------------------------------------
# processors
# ---------------------------------------------------------------------------


def test_get_processor_configs_site_overrides_general(adapter):
    procs = adapter.get_processor_configs("example")
    assert len(procs) == 1
    p = procs[0]
    assert isinstance(p, ProcessorConfig)
    assert p.name == "site-only"
    assert p.overwrite is False
    assert p.options == {"bar": 2}


def test_get_processor_configs_falls_back_to_general(adapter):
    procs = adapter.get_processor_configs("no_site_specific")
    assert len(procs) == 2
    names = [p.name for p in procs]
    assert names == ["normalize", "cleanup"]


# ---------------------------------------------------------------------------
# book ids
# ---------------------------------------------------------------------------


def test_get_book_ids_normalization(adapter):
    books = adapter.get_book_ids("example")
    assert len(books) == 3
    assert all(isinstance(b, BookConfig) for b in books)

    b1, b2, b3 = books

    assert b1.book_id == "123"
    assert b1.start_id is None
    assert b1.end_id is None
    assert b1.ignore_ids == frozenset()

    assert b2.book_id == "456"
    assert b2.start_id is None
    assert b2.end_id is None
    assert b2.ignore_ids == frozenset()

    assert b3.book_id == "789"
    assert b3.start_id == "1"
    assert b3.end_id == "2"
    assert b3.ignore_ids == frozenset({"3", "4"})


def test_get_book_ids_invalid_shape_raises():
    adapter = ConfigAdapter({"sites": {"bad": {"book_ids": 3.14}}})
    with pytest.raises(ValueError):
        adapter.get_book_ids("bad")


# ---------------------------------------------------------------------------
# logging and dirs
# ---------------------------------------------------------------------------


def test_get_log_level(adapter):
    assert adapter.get_log_level() == "DEBUG"

    adapter2 = ConfigAdapter({})
    assert adapter2.get_log_level() == "INFO"


def test_get_log_and_data_dirs(tmp_path):
    cfg = {
        "general": {
            "debug": {"log_dir": str(tmp_path / "logs")},
            "cache_dir": str(tmp_path / "cache"),
            "raw_data_dir": str(tmp_path / "raw"),
            "output_dir": str(tmp_path / "out"),
        }
    }
    adapter = ConfigAdapter(cfg)

    assert adapter.get_log_dir() == (tmp_path / "logs").resolve()
    assert adapter.get_cache_dir() == (tmp_path / "cache").resolve()
    assert adapter.get_raw_data_dir() == (tmp_path / "raw").resolve()
    assert adapter.get_output_dir() == (tmp_path / "out").resolve()


def test_get_dirs_defaults_when_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    adapter = ConfigAdapter({})
    assert adapter.get_cache_dir().name == "novel_cache"
    assert adapter.get_raw_data_dir().name == "raw_data"
    assert adapter.get_output_dir().name == "downloads"
    assert adapter.get_log_dir().name == "logs"
    assert adapter.get_cache_dir().is_absolute()


# ---------------------------------------------------------------------------
# _gen_cfg / _site_cfg
# ---------------------------------------------------------------------------


def test_gen_and_site_cfg_graceful_on_invalid():
    adapter = ConfigAdapter(
        {
            "general": [],
            "sites": {"x": "not-dict"},
        }
    )

    assert adapter._gen_cfg() == {}
    assert adapter._site_cfg("x") == {}
    assert adapter._site_cfg("y") == {}


# ---------------------------------------------------------------------------
# _dict_to_book_cfg
# ---------------------------------------------------------------------------


def test_dict_to_book_cfg_success():
    data = {
        "book_id": 123,
        "start_id": 1,
        "end_id": 2,
        "ignore_ids": [3, "4"],
    }
    cfg = ConfigAdapter._dict_to_book_cfg(data)
    assert isinstance(cfg, BookConfig)
    assert cfg.book_id == "123"
    assert cfg.start_id == "1"
    assert cfg.end_id == "2"
    assert cfg.ignore_ids == frozenset({"3", "4"})


def test_dict_to_book_cfg_missing_book_id():
    with pytest.raises(ValueError):
        ConfigAdapter._dict_to_book_cfg({})


# ---------------------------------------------------------------------------
# _dict_to_ocr_cfg
# ---------------------------------------------------------------------------


def test_dict_to_ocr_cfg_normalization():
    raw = {
        "model_name": "m",
        "model_dir": "/tmp/model",
        "input_shape": [1, 2, 3],
        "device": "cuda",
        "precision": "fp16",
        "cpu_threads": 8,
        "enable_hpi": True,
    }
    cfg = ConfigAdapter._dict_to_ocr_cfg(raw)
    assert isinstance(cfg, OCRConfig)
    assert cfg.model_name == "m"
    assert cfg.model_dir == "/tmp/model"
    assert cfg.input_shape == (1, 2, 3)
    assert cfg.device == "cuda"
    assert cfg.precision == "fp16"
    assert cfg.cpu_threads == 8
    assert cfg.enable_hpi is True


def test_dict_to_ocr_cfg_non_dict_returns_default():
    cfg = ConfigAdapter._dict_to_ocr_cfg("not-dict")
    assert isinstance(cfg, OCRConfig)


# ---------------------------------------------------------------------------
# _to_processor_cfgs
# ---------------------------------------------------------------------------


def test_to_processor_cfgs_filters_and_normalizes():
    rows = [
        {"name": "  A  ", "overwrite": True, "k": 1},
        {"name": ""},  # filtered
        {"not_name": "x"},  # filtered
        "not-dict",  # filtered
    ]
    procs = ConfigAdapter._to_processor_cfgs(rows)
    assert len(procs) == 1
    p = procs[0]
    assert isinstance(p, ProcessorConfig)
    assert p.name == "a"  # lower + strip
    assert p.overwrite is True
    assert p.options == {"k": 1}
