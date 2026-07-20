from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, APIKeyQuery

from confMagr import ConfMagr


class AuthException(Exception):
    def __init__(self, detail: str, status_code: int = 401):
        self.detail = detail
        self.status_code = status_code


api_key_query = APIKeyQuery(name="api_key", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    query_key: str | None = Depends(api_key_query),
    header_key: str | None = Depends(api_key_header),
) -> None:
    if not ConfMagr.AUTH_ENABLED:
        return

    path = request.url.path
    for wl in ConfMagr.AUTH_WHITELIST:
        if wl and (path == wl or path.startswith(f"{wl}/")):
            return

    api_key = query_key or header_key
    if not api_key:
        raise AuthException("缺少鉴权凭证（X-API-Key 或 api_key）")

    if api_key not in ConfMagr.API_KEYS:
        raise AuthException("无效的 API Key", status_code=403)
