from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base


@HandlerRegistry.register
class QQLuomuContentHandler(ContentBaseHandler):
    path = "/qq_luomu/content"
    name = "qq_luomu_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id"]
    description = "qq阅读（落幕）正文（仅支持小说）"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")
        item_id = kwargs.get("item_id", "")

        url = f"{base_url}/content?source=QQ阅读&book_id={book_id}&item_id={item_id}&tab=小说"
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await self.fetch(client, url)
            resp.raise_for_status()
            content_list = resp.json().get("data", {}).get("content", [])
            content = "\n".join(content_list) if isinstance(content_list, list) else str(content_list)
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": str(e)})
        return ContentResponse(contentType="novel", data={"content": content})
