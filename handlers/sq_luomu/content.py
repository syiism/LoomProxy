from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base


@HandlerRegistry.register
class SqLuomuContentHandler(ContentBaseHandler):
    path = "/sq_luomu/content"
    name = "sq_luomu_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id"]
    description = "书旗（落幕）正文"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")
        item_id = kwargs.get("item_id", "")

        url = f"{base_url}/content?source=书旗&book_id={book_id}&item_id={item_id}&tab=小说"
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return ContentResponse(contentType="novel", data=dict(data))
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": str(e)})
