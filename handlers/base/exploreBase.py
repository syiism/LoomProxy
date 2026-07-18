from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from . import BaseHandler
from ..base.searchBase import BookItem


class ExploreResponse(BaseModel):
    """探索接口返回结构 —— bookList 为 BookItem 数组"""
    bookList: list[BookItem]


class ExploreBaseHandler(BaseHandler):
    """探索基础处理器（抽象基类）"""
    response_model = ExploreResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> ExploreResponse:
        pass
