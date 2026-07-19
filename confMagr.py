from __future__ import annotations


class ConfMagr:
    # HTTP timeout 参数（裸值，由使用方构造 httpx.Timeout）
    TIMEOUT_CONNECT: float = 5.0
    TIMEOUT_POOL: float = 10.0

    # 缓存
    CACHE_TTL: int = 300
    CACHE_MAXSIZE: int = 128

    # 服务
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8081
    SERVER_LOG_LEVEL: str = "info"

    # 时区
    TZ_OFFSET_HOURS: int = 8

    # 通用错误码
    ERROR_CODE: int = -1

    # 静态数据文件
    UTILS_DIRNAME: str = "utils"
    DATA_DIR_SUFFIX: str = "_data"
    DATA_FILE_GLOB: str = "{source}_*.json"
