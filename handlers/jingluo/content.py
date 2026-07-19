from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base
from utils.fq_utils import _detect_book_type


async def _fetch_novel(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url}/content?item_id={item_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return ContentResponse(contentType="novel", data=dict(data))
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_audio(fetch, base_url: str, item_id: str, tone_id: str) -> ContentResponse:
    url = f"{base_url}/content?item_ids={item_id}&ts=听书&tone_id={tone_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return ContentResponse(contentType="audio", data={
            "content": data.get("content", ""),
            "backup_content": data.get("backup_url", ""),
            "duration": data.get("duration", 0),
            "definition": data.get("quality", ""),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_manga(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url}/manga?item_ids={item_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        images = resp.json().get("data", {}).get("images", [])
        content = "".join(f'<img src="{img}">\n' for img in images)
        return ContentResponse(contentType="manga", data={"content": content, "total": len(images)})
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_video(fetch, base_url: str, item_id: str, quality: str) -> ContentResponse:
    url = f"{base_url}/video?item_id={item_id}&type=json"
    if quality:
        url += f"&quality={quality}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return ContentResponse(contentType="video", data={
            "content": data.get("url", ""),
            "backup_content": data.get("backup_url", ""),
            "definition": data.get("definition", quality),
            "duration": data.get("duration", 0),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


@HandlerRegistry.register
class JingluoContentHandler(ContentBaseHandler):
    path = "/jingluo/content"
    name = "jingluo_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id", "tone_id", "quality"]
    description = "番茄（鲸落）统一内容（自动识别类型分发）"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "")
        book_id = kwargs.get("book_id", "")

        try:
            url = f"{base_url}/detail?book_id={book_id}"
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await self.fetch(client, url)
            resp.raise_for_status()
            book_type = _detect_book_type(resp.json().get("data", {}))
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": f"无法获取书籍类型: {e}"})

        item_id = kwargs.get("item_id", "")

        if book_type == "xiaoshuo":
            return await _fetch_novel(self.fetch, base_url, item_id)
        elif book_type == "tingshu":
            return await _fetch_audio(self.fetch, base_url, item_id, kwargs.get("tone_id", "0"))
        elif book_type == "manhua":
            return await _fetch_manga(self.fetch, base_url, item_id)
        elif book_type in ("duanju", "manju"):
            return await _fetch_video(self.fetch, base_url, item_id, kwargs.get("quality", ""))
        return ContentResponse(contentType="error", data={"message": f"未知书籍类型: {book_type}"})
