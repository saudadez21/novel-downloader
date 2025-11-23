import json

import aiohttp.web
import pytest
import pytest_asyncio
from novel_downloader.infra.sessions._curl_cffi import CurlCffiSession
from novel_downloader.schemas import FetcherConfig


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


@pytest.fixture
def cfg(tmp_path):
    return FetcherConfig(
        timeout=5,
        headers={"User-Agent": "pytest"},
        trust_env=False,
        verify_ssl=False,
        max_connections=5,
        impersonate="chrome",
    )


@pytest.mark.asyncio
async def test_init_and_close(cfg):
    s = CurlCffiSession(cfg, cookies=None)
    assert s._session is None

    await s.init()
    assert s._session is not None

    await s.close()
    assert s._session is None


@pytest.mark.asyncio
async def test_get_request(test_server, cfg):
    s = CurlCffiSession(cfg, cookies=None)
    await s.init()

    url = test_server.make_url("/ok")
    resp = await s.get(str(url))

    assert resp.status == 200
    assert resp.text == "hello"
    assert resp.ok

    await s.close()


@pytest.mark.asyncio
async def test_post_request(test_server, cfg):
    s = CurlCffiSession(cfg, cookies=None)
    await s.init()

    url = test_server.make_url("/post")
    resp = await s.post(str(url), json={"a": 1})

    assert resp.ok
    assert resp.json() == {"received": {"a": 1}}

    await s.close()


@pytest.mark.asyncio
async def test_session_property_error(cfg):
    s = CurlCffiSession(cfg, cookies=None)
    with pytest.raises(RuntimeError):
        _ = s.session


@pytest.mark.asyncio
async def test_cookies_save_load(tmp_path, test_server, cfg):
    cookie_dir = tmp_path / "cookies"
    s = CurlCffiSession(cfg, cookies=None)
    await s.init()

    # request that sets cookie
    url = test_server.make_url("/set-cookie")
    await s.get(str(url))

    # save cookies
    assert s.save_cookies(cookie_dir)

    saved = json.loads((cookie_dir / "curl_cffi.cookies").read_text())
    assert saved[0]["name"] == "token"
    assert saved[0]["value"] == "abc123"

    # load into new session
    s2 = CurlCffiSession(cfg, cookies=None)
    await s2.init()

    assert s2.load_cookies(cookie_dir)
    assert s2.get_cookie("token") == "abc123"

    await s.close()
    await s2.close()


@pytest.mark.asyncio
async def test_cookie_update_and_clear(cfg):
    s = CurlCffiSession(cfg, cookies=None)
    await s.init()

    s.update_cookies({"k": "v"})
    assert s.get_cookie("k") == "v"

    s.clear_cookie("k")
    assert s.get_cookie("k") is None

    s.update_cookies({"a": "1", "b": "2"})
    s.clear_cookies()
    assert s.get_cookie("a") is None
    assert s.get_cookie("b") is None

    await s.close()
