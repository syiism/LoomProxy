from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from .base import BaseHandler


class BookDetail(BaseModel):
    bookType: str
    bookTypeCode: int
    authorId: str
    bookId: str
    name: str
    aliasName: str
    author: str
    status: str
    createTime: str
    lastUpdateTime: str
    wordCount: str
    category: str
    tags: str
    roles: str
    tones: str
    score: str
    readCount: str
    source: str
    intro: str
    copyright: str
    bookReview: str
    coverUrl: str
    lastChapter: str


class DetailBaseHandler(BaseHandler):
    response_model = BookDetail

    @abstractmethod
    async def handle(self, **kwargs: Any) -> BookDetail:
        pass
