from __future__ import annotations

from typing import Any

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import _detect_book_type, normalize_api_base


async def _fetch_novel(fetch, api_base: str, item_id: str, tab: str) -> ContentResponse:
    url = f"{api_base}/content?source=番茄&item_id={item_id}&tab={tab}"
    try:
        resp = await fetch(url)
        resp.raise_for_status()
        content = resp.json().get("data", {}).get("content", "")
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    return ContentResponse(contentType="novel", data={"content": content})


async def _fetch_manga(fetch, api_base: str, item_id: str) -> ContentResponse:
    url = f"{api_base}/content?item_id={item_id}&tab=漫画&source=番茄&cmd=1"
    try:
        resp = await fetch(url)
        resp.raise_for_status()
        images_html = resp.json().get("data", {}).get("images", "")
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    return ContentResponse(contentType="manga", data={"content": images_html})


async def _fetch_audio(fetch, api_base: str, item_id: str, tone_id: str) -> ContentResponse:
    url = f"{api_base}/content?item_id={item_id}&tab=听书&tone_id={tone_id}&source=番茄"
    try:
        resp = await fetch(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return ContentResponse(contentType="audio", data={
            "content": data.get("audio_url", ""),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_video(fetch, api_base: str, item_id: str, tab: str) -> ContentResponse:
    url = f"{api_base}/content?item_id={item_id}&tab={tab}&source=番茄&cmd=1"
    try:
        resp = await fetch(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return ContentResponse(contentType="video", data={
            "content": (api_base + data.get('video_url', '')).replace('apiapi', 'api')
            })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


@HandlerRegistry.register
class LuomuContentHandler(ContentBaseHandler):
    path = "/luomu/content"
    name = "luomu_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id", "tone_id", "quality"]
    description = "番茄（落幕）统一内容（自动识别类型分发：小说/漫画/听书/短剧/漫剧，source=番茄 硬编码）"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")
        tab = kwargs.get("tab", "小说")

        try:
            url = f"{base_url}/detail?source=番茄&book_id={book_id}"
            resp = await self.fetch(url)
            resp.raise_for_status()
            book_type = _detect_book_type(resp.json().get("data", {}))
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": f"无法获取书籍类型: {e}"})

        item_id = kwargs.get("item_id", "")

        if book_type == "novel":
            return await _fetch_novel(self.fetch, api_base=base_url, item_id=item_id, tab=tab)
        elif book_type == "manga":
            return await _fetch_manga(self.fetch, api_base=base_url, item_id=item_id)
        elif book_type == "audio":
            return await _fetch_audio(self.fetch, api_base=base_url, item_id=item_id, tone_id=kwargs.get("tone_id", "1"))
        elif book_type == "video":
            return await _fetch_video(self.fetch, api_base=base_url, item_id=item_id, tab="短剧")
        return ContentResponse(contentType="error", data={"message": f"未知书籍类型: {book_type}"})
