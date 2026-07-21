from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ[key])
    except (KeyError, ValueError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ[key])
    except (KeyError, ValueError):
        return default


class ConfMagr:
    # HTTP timeout 参数（裸值，由使用方构造 httpx.Timeout）
    TIMEOUT_CONNECT: float = _env_float("TIMEOUT_CONNECT", 5.0)
    TIMEOUT_POOL: float = _env_float("TIMEOUT_POOL", 10.0)

    # 缓存
    CACHE_TTL: int = _env_int("CACHE_TTL", 300)
    CACHE_MAXSIZE: int = _env_int("CACHE_MAXSIZE", 128)

    # 服务
    SERVER_HOST: str = _env("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = _env_int("SERVER_PORT", 8081)
    SERVER_LOG_LEVEL: str = _env("SERVER_LOG_LEVEL", "info")

    # 时区
    TZ_OFFSET_HOURS: int = _env_int("TZ_OFFSET_HOURS", 8)

    # 通用错误码
    ERROR_CODE: int = _env_int("ERROR_CODE", -1)

    # 静态数据文件
    DATA_DIR: str = _env("DATA_DIR", "data")
    DATA_FILE_GLOB: str = _env("DATA_FILE_GLOB", "*.json")

    # 鉴权
    AUTH_ENABLED: bool = _env("AUTH_ENABLED", "false").lower() == "true"
    API_KEYS: list[str] = [k.strip() for k in _env("API_KEYS", "").split(",") if k.strip()]
    AUTH_WHITELIST: list[str] = [k.strip() for k in _env("AUTH_WHITELIST", "/,/datasources,/data").split(",")]
