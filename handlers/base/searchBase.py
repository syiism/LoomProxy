from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from . import BaseHandler


class BookItem(BaseModel):
    """单条书籍信息"""
    bookId: str
    name: str
    author: str
    kind: str
    wordCount: str
    lastChapter: str
    intro: str
    coverUrl: str


class SearchResponse(BaseModel):
    """搜索接口返回结构 —— bookList 为 BookItem 数组"""
    bookList: list[BookItem]


class SearchBaseHandler(BaseHandler):
    """搜索基础处理器（抽象基类）"""
    response_model = SearchResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> SearchResponse:
        pass
