"""
Handler 基类与注册表 —— 实现开闭原则：
- 对扩展开放：新增接口只需在 handlers/ 目录下新增一个文件，继承 BaseHandler 即可
- 对修改封闭：app.py 核心启动逻辑无需改动
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import httpx

from confMagr import ConfMagr


class HandlerRegistry:
    _items: ClassVar[dict[str, type["BaseHandler"]]] = {}

    @classmethod
    def register(cls, name_or_cls: str | type["BaseHandler"] | None = None):
        if callable(name_or_cls) and isinstance(name_or_cls, type):
            cls._items[name_or_cls.__name__] = name_or_cls
            return name_or_cls
        def decorator(target_cls: type["BaseHandler"]) -> type["BaseHandler"]:
            key = name_or_cls if isinstance(name_or_cls, str) else target_cls.__name__
            cls._items[key] = target_cls
            return target_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> type["BaseHandler"] | None:
        return cls._items.get(name)

    @classmethod
    def all(cls) -> list[type["BaseHandler"]]:
        return list(cls._items.values())


class BaseHandler(ABC):
    path: str = ""
    name: str | None = None
    methods: list[str] = ["GET"]
    query_params: list[str] = []
    description: str = ""

    async def fetch(
        self,
        url: str,
        method: str = "GET",
        **kwargs: Any,
    ) -> httpx.Response:
        timeout = kwargs.pop("timeout", httpx.Timeout(ConfMagr.TIMEOUT_POOL, connect=ConfMagr.TIMEOUT_CONNECT))
        follow_redirects = kwargs.pop("follow_redirects", True)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects) as client:
            return await client.request(method, url, **kwargs)

    @abstractmethod
    async def handle(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError
