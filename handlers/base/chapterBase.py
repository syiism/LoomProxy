from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional

from pydantic import BaseModel

from . import BaseHandler


class ChapterItem(BaseModel):
    """单条章节信息"""
    title: str
    itemId: str
    chapterInfo: str


class ChapterResponse(BaseModel):
    """章节接口返回结构 —— 缺失以下任一字段将在构造时抛出 ValidationError。"""
    chapterList: list[ChapterItem]
    nextTocUrl: Optional[str] = None


class ChapterBaseHandler(BaseHandler):
    """章节基础处理器（抽象基类）"""
    response_model = ChapterResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> ChapterResponse:
        pass
