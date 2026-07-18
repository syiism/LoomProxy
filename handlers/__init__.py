"""handlers 包：自动发现并注册所有处理器"""

from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

# 导入 base 下的处理器模块，触发 @HandlerRegistry.register
from .base import BaseHandler, HandlerRegistry

if TYPE_CHECKING:
    pass


def _auto_discover() -> None:
    """遍历本包下的所有模块，触发 @register 的执行"""
    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name == "base":
            continue
        importlib.import_module(f"{__name__}.{module_info.name}")


def get_all_handlers() -> list[type[BaseHandler]]:
    _auto_discover()
    return HandlerRegistry.all()


__all__ = ["BaseHandler", "HandlerRegistry", "get_all_handlers"]
