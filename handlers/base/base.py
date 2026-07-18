"""
Handler 基类与注册表 —— 实现开闭原则：
- 对扩展开放：新增接口只需在 handlers/ 目录下新增一个文件，继承 BaseHandler 即可
- 对修改封闭：app.py 核心启动逻辑无需改动
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class HandlerRegistry:
    """全局 Handler 注册表 —— 支持有参/无参两种装饰器用法。

    - 无参：``@register``  —— 以类名作为 key
    - 带参：``@register("name")``  —— 以指定名称作为 key
    """

    _items: ClassVar[dict[str, type["BaseHandler"]]] = {}

    @classmethod
    def register(cls, name_or_cls: str | type["BaseHandler"] | None = None):
        """装饰器：注册一个类，支持有参和无参两种用法。"""
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
    """所有 GET/API 处理器的抽象基类"""

    # 必须由子类定义：FastAPI 路由路径
    path: str = ""
    # 可选：路由名
    name: str | None = None
    # 支持的 HTTP 方法
    methods: list[str] = ["GET"]
    # 接收的 query 参数名列表（字符串形式），由子类声明
    query_params: list[str] = []
    # 简介
    description: str = ""

    @abstractmethod
    async def handle(self, **kwargs: Any) -> dict[str, Any]:
        """处理请求并返回 JSON 可序列化的结果"""
        raise NotImplementedError
