from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base
from utils.fq_utils import _detect_book_type


async def _fetch_novel(api_base: str, item_id: str) -> ContentResponse:
    url = f"{api_base.rstrip('/')}/content?item_ids={item_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        content = resp.json().get("data", {}).get("content", "")
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    return ContentResponse(contentType="novel", data={"content": content})


async def _fetch_audio(api_base: str, item_id: str, tone_id: str) -> ContentResponse:
    url = f"{api_base.rstrip('/')}/content?item_ids={item_id}&ts=听书&tone_id={tone_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
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


async def _fetch_manga(api_base: str, item_id: str) -> ContentResponse:
    url = f"{api_base.rstrip('/')}/manga?item_ids={item_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        images = resp.json().get("data", {}).get("images", [])
        content = "".join(f'<img src="{img}">\n' for img in images)
        return ContentResponse(contentType="manga", data={"content": content, "total": len(images)})
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_video(api_base: str, item_id: str, book_id: str, quality: str) -> ContentResponse:
    url = f"{api_base.rstrip('/')}/video?item_id={item_id}&book_id={book_id}&type=json"
    if quality:
        url += f"&quality={quality}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
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
class MufanContentHandler(ContentBaseHandler):
    path = "/mufan/content"
    name = "mufan_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id", "tone_id", "quality"]
    description = "mufan 统一内容（自动识别类型分发：小说/听书/漫画/短剧/漫剧）"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = kwargs.get("base_url", "").rstrip("/")
        api_base = normalize_api_base(base_url, "/api")
        book_id = kwargs.get("book_id", "")

        try:
            url = f"{api_base}/detail?book_id={book_id}"
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            book_type = _detect_book_type(resp.json().get("data", {}))
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": f"无法获取书籍类型: {e}"})

        item_id = kwargs.get("item_id", "")

        if book_type == "xiaoshuo":
            return await _fetch_novel(api_base, item_id)
        elif book_type == "tingshu":
            return await _fetch_audio(api_base, item_id, kwargs.get("tone_id", "0"))
        elif book_type == "manhua":
            return await _fetch_manga(api_base, item_id)
        elif book_type in ("duanju", "manju"):
            return await _fetch_video(api_base, item_id, book_id, kwargs.get("quality", ""))
        return ContentResponse(contentType="error", data={"message": f"未知书籍类型: {book_type}"})
