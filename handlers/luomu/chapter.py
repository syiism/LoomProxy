from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from base.base import HandlerRegistry
from base.chapterBase import ChapterBaseHandler, ChapterItem, ChapterResponse
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, normalize_api_base


def build_chapter_info(item: dict[str, Any]) -> str:
    volume = item.get("volume_name", "")
    ts_str = item.get("firstPassTime", "")
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
        itemId=item.get("itemId", ""),
        chapterInfo=build_chapter_info(item),
    )


@HandlerRegistry.register
class LuomuChapterHandler(ChapterBaseHandler):
    path = "/luomu/chapter"
    name = "luomu_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "luomu 章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/directory?source=番茄&book_id={book_id}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        inner = data.get("data", {})
        raw_list = inner.get("chapterListWithVolume", [])
        chapter_list: list[ChapterItem] = []
        for volume in raw_list:
            if isinstance(volume, list):
                for item in volume:
                    if isinstance(item, dict) and item.get("itemId"):
                        chapter_list.append(build_chapter_item(item))

        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)
