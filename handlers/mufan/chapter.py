from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from base.base import HandlerRegistry
from base.chapterBase import ChapterBaseHandler, ChapterItem, ChapterResponse
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, normalize_api_base


def build_chapter_info(item: dict[str, Any]) -> str:
    volume = item.get("volume_name", "")
    ts_str = item.get("first_pass_time", "")
    if not ts_str:
        return volume
    try:
        ts = int(ts_str)
        if ts > 1e12:
            ts //= 1000
        dt = datetime.fromtimestamp(ts, tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        return f"{volume} - {dt}" if volume else dt
    except (ValueError, OSError):
        return volume


def build_chapter_item(item: dict[str, Any]) -> ChapterItem:
    return ChapterItem(
        title=item.get("title", ""),
        itemId=item.get("item_id", ""),
        chapterInfo=build_chapter_info(item),
    )


@HandlerRegistry.register
class MufanChapterHandler(ChapterBaseHandler):
    path = "/mufan/chapter"
    name = "mufan_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "番茄（沐凡）章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = kwargs.get("base_url", "").rstrip("/")
        api_base = normalize_api_base(base_url, "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{api_base}/directory?book_id={book_id}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        raw_list = data.get("item_data_list", [])
        chapter_list = [build_chapter_item(item) for item in raw_list]

        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)
