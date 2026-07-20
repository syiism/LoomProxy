from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


def test_root_health(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert len(data["endpoints"]) > 0


def test_datasources_cached(client):
    r = client.get("/datasources")
    assert r.status_code == 200
    data = r.json()
    assert "names" in data
    assert len(data["names"]) > 0


def test_ssrf_blocked(client):
    r = client.get("/tutu/search?base_url=http://127.0.0.1&query=test")
    assert r.status_code == 400
    assert "不安全的 base_url" in r.json()["msg"]


def test_ssrf_blocked_private(client):
    r = client.get("/tutu/search?base_url=http://10.0.0.1&query=test")
    assert r.status_code == 400


def test_ssrf_blocked_localhost(client):
    r = client.get("/tutu/search?base_url=http://localhost:8080&query=test")
    assert r.status_code == 400


def test_auth_disabled_by_default(client):
    """鉴权默认关闭，请求无需 Key（SSRF 校验优先）"""
    r = client.get("/tutu/search?base_url=http://10.0.0.1&query=test")
    assert r.status_code == 400  # SSRF 拦截，说明越过了鉴权


def test_auth_enabled_no_key(client):
    """开启鉴权后，无 Key 请求返回 401"""
    from confMagr import ConfMagr
    saved_enabled = ConfMagr.AUTH_ENABLED
    ConfMagr.AUTH_ENABLED = True
    saved_keys = ConfMagr.API_KEYS
    ConfMagr.API_KEYS = ["test-key"]
    try:
        r = client.get("/tutu/search?base_url=http://10.0.0.1&query=test")
        assert r.status_code == 401
        assert "缺少鉴权凭证" in r.json()["msg"]
    finally:
        ConfMagr.AUTH_ENABLED = saved_enabled
        ConfMagr.API_KEYS = saved_keys


def test_auth_enabled_invalid_key(client):
    """开启鉴权后，无效 Key 返回 403"""
    from confMagr import ConfMagr
    saved_enabled = ConfMagr.AUTH_ENABLED
    ConfMagr.AUTH_ENABLED = True
    saved_keys = ConfMagr.API_KEYS
    ConfMagr.API_KEYS = ["valid-key"]
    try:
        r = client.get(
            "/tutu/search?base_url=http://10.0.0.1&query=test",
            headers={"X-API-Key": "wrong-key"},
        )
        assert r.status_code == 403
        assert "无效的 API Key" in r.json()["msg"]
    finally:
        ConfMagr.AUTH_ENABLED = saved_enabled
        ConfMagr.API_KEYS = saved_keys


def test_auth_enabled_valid_key(client):
    """开启鉴权后，有效 Key 可正常访问（SSRF 校验优先）"""
    from confMagr import ConfMagr
    saved_enabled = ConfMagr.AUTH_ENABLED
    ConfMagr.AUTH_ENABLED = True
    saved_keys = ConfMagr.API_KEYS
    ConfMagr.API_KEYS = ["valid-key"]
    try:
        r = client.get(
            "/tutu/search?base_url=http://10.0.0.1&query=test",
            headers={"X-API-Key": "valid-key"},
        )
        assert r.status_code == 400  # SSRF 拦截，说明过了鉴权
    finally:
        ConfMagr.AUTH_ENABLED = saved_enabled
        ConfMagr.API_KEYS = saved_keys


def test_auth_whitelist_bypass(client):
    """开启鉴权后，白名单路径免鉴权"""
    from confMagr import ConfMagr
    saved_enabled = ConfMagr.AUTH_ENABLED
    ConfMagr.AUTH_ENABLED = True
    try:
        r = client.get("/datasources")
        assert r.status_code == 200  # 在白名单中，无需 Key
    finally:
        ConfMagr.AUTH_ENABLED = saved_enabled


@pytest.mark.asyncio
async def test_fetch_method_mockable():
    """BaseHandler.fetch 可以被 mock，无需真实网络请求"""
    from handlers.tutu.search import TutuSearchHandler
    handler = TutuSearchHandler()

    mock_response = httpx.Response(200, json={"data": "ok"})
    handler.fetch = AsyncMock(return_value=mock_response)
    async with httpx.AsyncClient() as client:
        resp = await handler.fetch(client, "http://example.com")
    assert resp.status_code == 200
