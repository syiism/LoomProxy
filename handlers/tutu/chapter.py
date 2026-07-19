from __future__ import annotations
from datetime import datetime
from typing import Any

from base.chapterBase import ChapterBaseHandler, ChapterResponse, ChapterItem
from base.base import HandlerRegistry
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, normalize_api_base


def parse_chapter_list_item(chapter_list_with_volume: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """递归解析分卷章节列表，收集所有章节数据。"""
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


def build_chapter_info(item: dict[str, Any]) -> str:
    """拼接章节信息：卷名-更新日期"""
    volume = item.get("volume_name", "")
    ts_str = item.get("firstPassTime") or item.get("last_publish_time") or item.get("update_time", "")
    if not ts_str:
        return volume
    try:
        ts = int(ts_str)
        if ts > 1e12:
            ts //= 1000
        create_time = datetime.fromtimestamp(ts, tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        return f"{volume} - {create_time}" if volume else create_time
    except (ValueError, OSError):
        return volume


def build_chapter_item(item: dict[str, Any]) -> ChapterItem:
    """构建章节Item"""
    return ChapterItem(
        title=item.get("title", ""),
        itemId=item.get("item_id", "") or item.get("itemId", ""),
        chapterInfo=build_chapter_info(item),
    )


@HandlerRegistry.register
class TutuChapterHandler(ChapterBaseHandler):
    """tutu 章节处理器"""
    path = "/tutu/chapter"
    name = "tutu_chapter"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "番茄（兔兔）章节"

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "")

        import httpx

        url = f"{base_url}/books/{book_id}/directory/fanqie"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        chapter_list_with_volume = data.get("data", {}).get("chapterListWithVolume", [])
        raw_list = parse_chapter_list_item(chapter_list_with_volume)
        chapter_list = [build_chapter_item(item) for item in raw_list]

        return ChapterResponse(chapterList=chapter_list, nextTocUrl=None)