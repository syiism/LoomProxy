from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional

from pydantic import BaseModel

from .base import BaseHandler


class ChapterItem(BaseModel):
    title: str
    itemId: str
    chapterInfo: str


class ChapterResponse(BaseModel):
    chapterList: list[ChapterItem]
    nextTocUrl: Optional[str] = None


class ChapterBaseHandler(BaseHandler):
    response_model = ChapterResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> ChapterResponse:
        pass
