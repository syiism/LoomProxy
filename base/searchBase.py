from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from .base import BaseHandler


class BookItem(BaseModel):
    bookId: str
    name: str
    author: str
    kind: str
    wordCount: str
    lastChapter: str
    intro: str
    coverUrl: str


class SearchResponse(BaseModel):
    bookList: list[BookItem]


class SearchBaseHandler(BaseHandler):
    response_model = SearchResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> SearchResponse:
        pass
