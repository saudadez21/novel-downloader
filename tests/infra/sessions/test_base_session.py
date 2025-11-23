import pytest
from novel_downloader.infra.sessions import create_session
from novel_downloader.schemas import FetcherConfig


@pytest.fixture
def cfg(tmp_path):
    return FetcherConfig(
        timeout=5,
        headers={"User-Agent": "pytest"},
        proxy=None,
        proxy_user=None,
        proxy_pass=None,
        trust_env=False,
        verify_ssl=False,
        max_connections=5,
    )


@pytest.mark.parametrize("backend", ["aiohttp", "httpx", "curl_cffi"])
@pytest.mark.asyncio
async def test_headers_returns_copy(backend, cfg):
    """BaseSession.headers should always return a copy."""
    session = create_session(backend, cfg, cookies=None)

    h1 = session.headers
    h2 = session.headers

    assert h1 == h2
    assert h1 is not h2

    # modifying the copy should not affect original headers
    h1["User-Agent"] = "modified"
    assert session.headers["User-Agent"] == "pytest"


@pytest.mark.parametrize("backend", ["aiohttp", "httpx", "curl_cffi"])
@pytest.mark.asyncio
async def test_async_context_manager_calls_init_and_close(backend, cfg):
    """`async with session:` should call init() and close()."""

    session = create_session(backend, cfg, cookies=None)

    # Should not have an active session yet
    assert session._session is None

    async with session as s2:
        # During context manager, session must be initialized
        assert s2._session is not None

    # After exiting context manager, the session must be closed
    assert session._session is None
