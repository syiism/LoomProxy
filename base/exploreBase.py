from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from .base import BaseHandler
from .searchBase import BookItem


class ExploreResponse(BaseModel):
    bookList: list[BookItem]


class ExploreBaseHandler(BaseHandler):
    response_model = ExploreResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> ExploreResponse:
        pass
