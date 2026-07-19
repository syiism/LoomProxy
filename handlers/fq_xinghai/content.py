from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import DEFAULT_TIMEOUT, _detect_book_type, normalize_api_base


async def _fetch_novel(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url.rstrip('/')}/chapters/{item_id}?filter=none&source=content"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        content = resp.json().get("data", {}).get("content", "")
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    return ContentResponse(contentType="novel", data={"content": content})


async def _fetch_audio(fetch, base_url: str, item_id: str, book_id: str, tone_id: str) -> ContentResponse:
    url = f"{base_url.rstrip('/')}/media/audio?item_id={item_id}&book_id={book_id}&tone_id={tone_id}&filter=none"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data") or []
        v1 = items[0] if isinstance(items, list) and items else None

        if not v1:
            return ContentResponse(contentType="error", data={"message": "无法获取音频"})

        return ContentResponse(contentType="audio", data={
            "content": v1.get("main_url", ""),
            "backup_content": v1.get("backup_url", ""),
            "quality": v1.get("quality", ""),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_manga(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url.rstrip('/')}/chapters/{item_id}/manga"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        images = resp.json().get("data", {}).get("images", [])
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    content = ""
    for img in images:
        content += f'<img src="{img}">\n'
    return ContentResponse(contentType="manga", data={"content": content, "total": len(images)})


async def _fetch_video(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url.rstrip('/')}/media/video?item_id={item_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        data = resp.json()
        play = data.get("data", {}).get("play", {})

        return ContentResponse(contentType="video", data={
            "content": play.get("play_url", ""),
            "decrypt_url": play.get("decrypt_url", ""),
            "cek": play.get("cek", ""),
            "proxy_url": play.get("proxy_url", ""),
            "quality": play.get("quality", ""),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


@HandlerRegistry.register
class XinghaiContentHandler(ContentBaseHandler):
    path = "/fq_xinghai/content"
    name = "fq_xinghai_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id", "tone_id", "quality"]
    description = "星海统一内容（自动识别类型分发：小说/听书/漫画/短剧/漫剧）"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "")

        try:
            url = f"{base_url.rstrip('/')}/books/{book_id}?filter=none&source=detail"
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await self.fetch(client, url)
            resp.raise_for_status()
            book_type = _detect_book_type(resp.json().get("data", {}))
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": f"无法获取书籍类型: {e}"})

        if book_type == "xiaoshuo":
            return await _fetch_novel(
                self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
            )
        elif book_type == "tingshu":
            return await _fetch_audio(
                self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
                book_id=book_id,
                tone_id=kwargs.get("tone_id", "0"),
            )
        elif book_type == "manhua":
            return await _fetch_manga(
                self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
            )
        elif book_type in ("duanju", "manju"):
            return await _fetch_video(
                self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
            )
        return ContentResponse(contentType="error", data={"message": f"未知书籍类型: {book_type}"})
