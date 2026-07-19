from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from base.base import HandlerRegistry
from base.chapterBase import ChapterBaseHandler, ChapterItem, ChapterResponse
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, normalize_api_base


def build_chapter_info(item: dict[str, Any]) -> str:
    volume = item.get("volume_name", "")
    chapter_order = item.get("real_chapter_order", "")
    return f"{volume} - 第{chapter_order}集" if volume else f"第{chapter_order}集"


def build_chapter_item(item: dict[str, Any]) -> ChapterItem:
    return ChapterItem(
        title=item.get("title", ""),
        itemId=item.get("item_id", ""),
        chapterInfo=build_chapter_info(item),
    )


@HandlerRegistry.register
class JingluoChapterHandler(ChapterBaseHandler):
    path = "/jingluo/chapter"
    name = "jingluo_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "番茄（鲸落）章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/catalog?book_id={book_id}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", {}).get("item_data_list", [])
        chapter_list = [build_chapter_item(item) for item in raw_list if item.get("item_id")]
        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)
