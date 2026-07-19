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
