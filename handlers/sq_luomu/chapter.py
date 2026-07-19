from __future__ import annotations

from typing import Any

import httpx
from datetime import datetime, timedelta, timezone

from base.base import HandlerRegistry
from base.chapterBase import ChapterBaseHandler, ChapterItem, ChapterResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base

TZ_SHANGHAI = timezone(timedelta(hours=8))

def build_chapter_item(item: dict[str, Any], volumeName: str) -> ChapterItem:
    ts = item.get("chapterUpdateTime")
    last_update = ""
    if ts:
        try:
            last_update = datetime.fromtimestamp(int(ts), tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return ChapterItem(
        title=item.get("chapterName", ""),
        itemId=str(item.get("chapterUrl", "")),
        chapterInfo=f"{volumeName} - {last_update}",
    )


@HandlerRegistry.register
class SqLuomuChapterHandler(ChapterBaseHandler):
    path = "/sq_luomu/chapter"
    name = "sq_luomu_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "书旗（落幕）章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/directory?source=书旗&book_id={book_id}&tab=小说"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        body = resp.json()

        volume_list = body.get("data", {}).get("chapterList", [])
        chapter_list: list[ChapterItem] = []
        for vol in volume_list:
            volumeName = vol.get("volumeName", "")
            for item in vol.get("volumeList", []):
                if item.get("chapterId"):
                    chapter_list.append(build_chapter_item(item, volumeName=volumeName))
        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)
