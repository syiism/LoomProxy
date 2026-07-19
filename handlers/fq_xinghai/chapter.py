from __future__ import annotations
from datetime import datetime
from typing import Any

import httpx

from base.chapterBase import ChapterBaseHandler, ChapterResponse, ChapterItem
from base.base import HandlerRegistry
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, normalize_api_base


def build_chapter_item(item: dict[str, Any]) -> ChapterItem:
    ts_str = item.get("firstPassTime") or item.get("last_publish_time") or item.get("update_time", "")
    chapter_info = ""
    if ts_str:
        try:
            ts = int(ts_str)
            if ts > 1e12:
                ts //= 1000
            chapter_info = datetime.fromtimestamp(ts, tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            pass

    volume = item.get("volume_name", "")
    if volume and chapter_info:
        chapter_info = f"{volume} - {chapter_info}"
    elif volume:
        chapter_info = volume

    return ChapterItem(
        title=item.get("title", ""),
        itemId=item.get("item_id", "") or item.get("itemId", ""),
        chapterInfo=chapter_info,
    )


@HandlerRegistry.register
class XinghaiChapterHandler(ChapterBaseHandler):
    path = "/fq_xinghai/chapter"
    name = "fq_xinghai_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "星海章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/books/{book_id}/toc?filter=none&source=web"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        chapter_list_with_volume = data.get("data", {}).get("chapterListWithVolume", [])
        raw_list = _parse_chapter_list(chapter_list_with_volume)
        chapter_list = [build_chapter_item(item) for item in raw_list]

        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)


def _parse_chapter_list(chapter_list_with_volume: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data_list: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        if "item_id" in node or "title" in node:
            data_list.append(node)
        for key in ("chapter_data", "data", "children"):
            if key in node and isinstance(node[key], list):
                walk(node[key])

    walk(chapter_list_with_volume)
    return data_list
