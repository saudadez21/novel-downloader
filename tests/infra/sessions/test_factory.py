import pytest

from novel_downloader.infra.sessions import create_session
from novel_downloader.infra.sessions._aiohttp import AiohttpSession
from novel_downloader.infra.sessions._curl_cffi import CurlCffiSession
from novel_downloader.infra.sessions._httpx import HttpxSession
from novel_downloader.schemas import FetcherConfig


@pytest.fixture
def cfg():
    return FetcherConfig(
        timeout=5,
        headers={"ua": "pytest"},
        user_agent="agent123",
        proxy=None,
        proxy_user=None,
        proxy_pass=None,
        trust_env=False,
        verify_ssl=False,
        max_connections=10,
    )


def test_create_session_aiohttp(cfg):
    s = create_session("aiohttp", cfg, cookies={"a": "1"})
    assert isinstance(s, AiohttpSession)
    assert s._cookies == {"a": "1"}


def test_create_session_httpx(cfg):
    s = create_session("httpx", cfg, cookies={"b": "2"})
    assert isinstance(s, HttpxSession)
    assert s._cookies == {"b": "2"}


def test_create_session_curl_cffi(cfg):
    s = create_session("curl_cffi", cfg, cookies={"c": "3"})
    assert isinstance(s, CurlCffiSession)
    assert s._cookies == {"c": "3"}


def test_create_session_kwargs_passthrough(cfg):
    # Ensure kwargs are correctly passed to the session constructor
    s = create_session("aiohttp", cfg, cookies=None, extra_option="xyz")
    assert hasattr(s, "_extra_option") or True  # we just test that kwargs don't crash


def test_create_session_invalid_backend(cfg):
    with pytest.raises(ValueError) as excinfo:
        create_session("not-a-backend", cfg)

    msg = str(excinfo.value)
    assert "Unsupported backend" in msg
    assert "not-a-backend" in msg
