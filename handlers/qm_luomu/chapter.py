from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.chapterBase import ChapterBaseHandler, ChapterItem, ChapterResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base


def build_chapter_item(item: dict[str, Any]) -> ChapterItem:
    return ChapterItem(
        title=item.get("chapterName", ""),
        itemId=str(item.get("chapterUrl", "")),
        chapterInfo=item.get("chapterUpdateTime", ""),
    )


@HandlerRegistry.register
class QmLuomuChapterHandler(ChapterBaseHandler):
    path = "/qm_luomu/chapter"
    name = "qm_luomu_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "七猫（落幕）章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/directory?source=七猫&book_id={book_id}&tab=小说"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", {}).get("chapter_lists", [])
        chapter_list = [build_chapter_item(item) for item in raw_list]
        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)
