from __future__ import annotations

import json
from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base
from utils.fq_utils import _detect_book_type


async def _fetch_novel(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url.rstrip('/')}/chapters/{item_id}/novel"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        content = resp.json().get("data", {}).get("content", "")
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    return ContentResponse(contentType="novel", data={"content": content})


async def _fetch_audio(fetch, base_url: str, item_id: str, book_id: str, tone_id: str) -> ContentResponse:
    async def _fetch(tid: str) -> dict[str, Any]:
        url = f"{base_url.rstrip('/')}/audio/play?item_ids={item_id}&book_id={book_id}&tone_id={tid}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url, method="POST")
        resp.raise_for_status()
        return resp.json()

    try:
        data = await _fetch(tone_id)
        video_model_raw = (
            data.get("data", {})
            .get("video_model_datas", [{}])[0]
            .get("video_model", "{}")
        )
        video_model = json.loads(video_model_raw) if isinstance(video_model_raw, str) else video_model_raw
        video_list = video_model.get("video_list", [])
        v1 = video_list[0] if video_list else None

        if not v1 and tone_id != "0":
            data = await _fetch("0")
            video_model_raw = (
                data.get("data", {})
                .get("video_model_datas", [{}])[0]
                .get("video_model", "{}")
            )
            video_model = json.loads(video_model_raw) if isinstance(video_model_raw, str) else video_model_raw
            video_list = video_model.get("video_list", [])
            v1 = video_list[0] if video_list else None

        if not v1:
            return ContentResponse(contentType="error", data={"message": "无法获取音频"})

        return ContentResponse(contentType="audio", data={
            "content": v1.get("main_url", ""),
            "backup_content": v1.get("backup_url", ""),
            "duration": video_model.get("video_duration", 0),
            "definition": v1.get("video_meta", {}).get("quality", ""),
            "bitrate": v1.get("video_meta", {}).get("bitrate", 0),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


async def _fetch_manga(fetch, base_url: str, item_id: str) -> ContentResponse:
    url = f"{base_url.rstrip('/')}/manga/{item_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await fetch(client, url)
        resp.raise_for_status()
        images = resp.json().get("data", {}).get("images", [])
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})
    content = ''
    for img in images:
        content += f'<img src="{img}">\n'
    return ContentResponse(contentType="manga", data={"content": content, "total": len(images)})


async def _fetch_video(fetch, base_url: str, video_ids: str, quality: str) -> ContentResponse:
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            if not quality:
                url = f"{base_url.rstrip('/')}/videos/multi?video_ids={video_ids}&list_qualities=1"
                resp = await fetch(client, url)
            else:
                url = f"{base_url.rstrip('/')}/videos/multi/{video_ids}?quality={quality}"
                resp = await fetch(client, url)
        resp.raise_for_status()
        body = resp.json()

        if not quality:
            video = (body.get("videos") or [{}])[0]
            return ContentResponse(contentType="video", data={
                "video_id": video.get("item_id", video_ids),
                "available": video.get("available", []),
                "qualities": video.get("qualities", []),
            })

        video_model = (
            body.get("response", {})
            .get("data", {})
            .get("video_model_datas", [{}])[0]
            .get("video_model", {})
        )
        video_list = video_model.get("video_list", [])
        v1 = video_list[0] if video_list else {}
        return ContentResponse(contentType="video", data={
            "content": v1.get("main_url", ""),
            "backup_content": v1.get("backup_url_1", ""),
            "definition": v1.get("video_meta", {}).get("definition", quality),
            "duration": video_model.get("video_duration", 0),
        })
    except Exception as e:
        return ContentResponse(contentType="error", data={"message": str(e)})


@HandlerRegistry.register
class TutuContentHandler(ContentBaseHandler):
    """tutu 统一内容处理器 — 根据 book_id 自动识别类型并分发"""
    path = "/tutu/content"
    name = "tutu_content"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "item_id", "tone_id", "quality"]
    description = "番茄（兔兔）统一内容（自动识别类型分发：小说/听书/漫画/短剧/漫剧）"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "")

        # 获取书籍类型
        try:
            url = f"{base_url.rstrip('/')}/books/{book_id}"
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await self.fetch(client, url)
            resp.raise_for_status()
            book_type = _detect_book_type(resp.json().get("data", {}))
        except Exception as e:
            return ContentResponse(contentType="error", data={"message": f"无法获取书籍类型: {e}"})

        if book_type == "xiaoshuo":
            return await _fetch_novel(
                fetch=self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
            )
        elif book_type == "tingshu":
            return await _fetch_audio(
                fetch=self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
                book_id=book_id,
                tone_id=kwargs.get("tone_id", "0"),
            )
        elif book_type == "manhua":
            return await _fetch_manga(
                fetch=self.fetch,
                base_url=base_url,
                item_id=kwargs.get("item_id", ""),
            )
        elif book_type in ("duanju", "manju"):
            return await _fetch_video(
                fetch=self.fetch,
                base_url=base_url,
                video_ids=kwargs.get("item_id", ""),
                quality=kwargs.get("quality", "720p"),
            )
        return ContentResponse(contentType="error", data={"message": f"未知书籍类型: {book_type}"})
