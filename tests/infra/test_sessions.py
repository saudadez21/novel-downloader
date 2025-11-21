# tests/test_sessions.py
from __future__ import annotations

import base64
import json
import pkgutil
from pathlib import Path
from typing import Any

import aiohttp
import aiohttp.web
import pytest
import pytest_asyncio
from novel_downloader.infra.sessions.base import BaseSession
from novel_downloader.schemas import FetcherConfig

# -----------------------------------------------------------------------------
# Single source of truth for supported backends in tests
# -----------------------------------------------------------------------------
SUPPORTED_BACKENDS: set[str] = {"aiohttp", "httpx", "curl_cffi"}


def safe_create(
    backend: str, cfg: FetcherConfig, cookies: dict[str, str] | None = None, **kw: Any
) -> BaseSession:
    """
    Create a session backend. If optional dependency for a backend
    is not installed, skip instead of failing the suite.
    """
    try:
        from novel_downloader.infra.sessions import create_session

        return create_session(backend, cfg, cookies=cookies, **kw)
    except ImportError as e:
        pytest.skip(f"backend {backend!r} not installed: {e}")


# ----------------------------
# Allow cookie acceptance from IP addresses during tests
# ----------------------------
@pytest.fixture(autouse=True)
def allow_ip_cookies(monkeypatch):
    """Allow cookie acceptance from IP addresses (e.g. 127.0.0.1) during tests."""
    import aiohttp.cookiejar

    monkeypatch.setattr(aiohttp.cookiejar, "is_ip_address", lambda host: False)


# ----------------------------
# aiohttp test server fixture
# ----------------------------
@pytest_asyncio.fixture
async def test_server(aiohttp_server):
    async def handler_ok(request):
        return aiohttp.web.Response(text="hello", status=200)

    async def handler_post(request):
        data = await request.json()
        return aiohttp.web.json_response({"received": data})

    async def handler_set_cookie(request):
        resp = aiohttp.web.Response(text="cookie!")
        resp.set_cookie("token", "abc123")
        return resp

    app = aiohttp.web.Application()
    app.router.add_get("/ok", handler_ok)
    app.router.add_post("/post", handler_post)
    app.router.add_get("/set-cookie", handler_set_cookie)

    server = await aiohttp_server(app)
    return server


# ----------------------------
# Fake proxy fixture
# ----------------------------
@pytest_asyncio.fixture
async def proxy_auth_server(aiohttp_server):
    """
    Fake proxy that enforces Basic proxy auth.
    Returns 407 until correct Proxy-Authorization is sent.
    """
    required_user = "user1"
    required_pass = "pass1"
    token = base64.b64encode(f"{required_user}:{required_pass}".encode()).decode()
    required_header = f"Basic {token}"

    seen = {
        "count": 0,
        "methods": [],
        "paths": [],
        "auth_headers": [],
        "authed_count": 0,
        "challenged_count": 0,
    }

    async def handler(request: aiohttp.web.Request):
        seen["count"] += 1
        seen["methods"].append(request.method)
        seen["paths"].append(request.raw_path)

        auth = request.headers.get("Proxy-Authorization")
        if auth:
            seen["auth_headers"].append(auth)

        if auth != required_header:
            seen["challenged_count"] += 1
            return aiohttp.web.Response(
                text="proxy auth required",
                status=407,
                headers={"Proxy-Authenticate": "Basic realm=proxy"},
            )

        seen["authed_count"] += 1
        return aiohttp.web.Response(text="proxied", status=200)

    app = aiohttp.web.Application()
    app.router.add_route("*", "/{tail:.*}", handler)

    server = await aiohttp_server(app)
    server.seen = seen
    server.required_user = required_user
    server.required_pass = required_pass
    server.required_header = required_header
    return server


@pytest_asyncio.fixture
async def proxy_noauth_server(aiohttp_server):
    """
    Minimal proxy that always returns 200 "proxied".
    Used only to prove the client routed through the proxy.
    """
    seen = {"count": 0, "methods": [], "paths": []}

    async def handler(request: aiohttp.web.Request):
        seen["count"] += 1
        seen["methods"].append(request.method)
        seen["paths"].append(request.raw_path)
        return aiohttp.web.Response(text="proxied", status=200)

    app = aiohttp.web.Application()
    app.router.add_route("*", "/{tail:.*}", handler)

    server = await aiohttp_server(app)
    server.seen = seen
    return server


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("backend", sorted(SUPPORTED_BACKENDS))
@pytest.mark.asyncio
async def test_factory_supports_all_backends(backend: str):
    """
    Fails if you add a backend to SUPPORTED_BACKENDS but forget to add a case
    under create_session().
    """
    cfg = FetcherConfig(backend=backend)
    session = safe_create(backend, cfg)
    assert isinstance(session, BaseSession)


@pytest.mark.parametrize("backend", sorted(SUPPORTED_BACKENDS))
@pytest.mark.asyncio
async def test_get_and_post_work(backend: str, test_server):
    cfg = FetcherConfig(backend=backend)
    base = str(test_server.make_url("/"))

    ok_url = base + "ok"
    post_url = base + "post"

    async with safe_create(backend, cfg) as s:
        r1 = await s.get(ok_url)
        assert r1.status == 200
        assert r1.content == b"hello"

        r2 = await s.post(post_url, json={"a": 1})
        assert r2.status == 200
        payload = json.loads(r2.content.decode("utf-8"))
        assert payload == {"received": {"a": 1}}


@pytest.mark.parametrize("backend", sorted(SUPPORTED_BACKENDS))
@pytest.mark.asyncio
async def test_proxy_is_used(backend: str, test_server, proxy_noauth_server):
    """
    If proxy is honored, response comes from proxy ("proxied").
    If ignored, response comes from origin ("hello").
    """
    cfg = FetcherConfig(
        backend=backend,
        proxy=str(proxy_noauth_server.make_url("/")),
        trust_env=False,
    )
    ok_url = str(test_server.make_url("/ok"))

    async with safe_create(backend, cfg) as s:
        r = await s.get(ok_url)

    assert r.content == b"proxied"
    assert proxy_noauth_server.seen["count"] >= 1


@pytest.mark.parametrize("backend", sorted(SUPPORTED_BACKENDS))
@pytest.mark.asyncio
async def test_proxy_auth_is_used(backend, test_server, proxy_auth_server):
    """
    Ensures proxy_user/proxy_pass are honored.
    """
    cfg = FetcherConfig(
        backend=backend,
        proxy=str(proxy_auth_server.make_url("/")),
        proxy_user=proxy_auth_server.required_user,
        proxy_pass=proxy_auth_server.required_pass,
        trust_env=False,
    )
    ok_url = str(test_server.make_url("/ok"))

    async with safe_create(backend, cfg) as s:
        r = await s.get(ok_url)

    assert r.content == b"proxied"

    # must have successfully authenticated at least once
    assert proxy_auth_server.seen["authed_count"] >= 1
    assert proxy_auth_server.required_header in proxy_auth_server.seen["auth_headers"]

    # challenged_count is allowed to be 0 (preemptive auth) or more (407 then retry)
    assert proxy_auth_server.seen["challenged_count"] >= 0


@pytest.mark.parametrize("backend", sorted(SUPPORTED_BACKENDS))
@pytest.mark.asyncio
async def test_cookies_set_and_persist(
    backend: str,
    test_server,
    tmp_path: Path,
):
    """
    Ensures:
      - cookies from server responses are stored
      - get_cookie works
      - save_cookies/load_cookies works
    """
    cfg = FetcherConfig(backend=backend)
    set_cookie_url = str(test_server.make_url("/set-cookie"))

    async with safe_create(backend, cfg) as s1:
        await s1.get(set_cookie_url)
        assert s1.get_cookie("token") == "abc123"
        assert s1.save_cookies(tmp_path)

    async with safe_create(backend, cfg) as s2:
        assert s2.load_cookies(tmp_path)
        assert s2.get_cookie("token") == "abc123"


def _discover_backend_keys() -> set[str]:
    """
    Auto-discover backend module names like _aiohttp.py -> "aiohttp".
    This makes sure SUPPORTED_BACKENDS stays in sync with available modules.
    """
    import novel_downloader.infra.sessions as sessions_pkg

    keys: set[str] = set()
    pkg_path = sessions_pkg.__path__  # type: ignore[attr-defined]
    for modinfo in pkgutil.iter_modules(pkg_path):
        name = modinfo.name
        if name.startswith("_"):
            keys.add(name[1:])
    return keys


def test_supported_backends_match_modules():
    """
    Optional guard:
    If you add a new file _newbackend.py but forget to include it in
    SUPPORTED_BACKENDS, this fails.
    """
    discovered = _discover_backend_keys()
    assert discovered <= SUPPORTED_BACKENDS
