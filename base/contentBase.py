from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from .base import BaseHandler


class ContentResponse(BaseModel):
    contentType: str
    data: dict[str, Any]


class ContentBaseHandler(BaseHandler):
    response_model = ContentResponse

    @abstractmethod
    async def handle(self, **kwargs: Any) -> ContentResponse:
        pass
