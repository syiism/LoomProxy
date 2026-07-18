from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any

from ..base.detailBase import BookDetail, DetailBaseHandler
from ..base.base import HandlerRegistry


def _format_time(ts_str: str) -> str:
    """时间戳转 YYYY-MM-dd HH:mm:ss（UTC+8）"""
    if not ts_str:
        return ""
    try:
        ts = int(ts_str)
        if ts > 1e12:
            ts = ts // 1000
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return ""


def _format_create_time(iso_str: str) -> str:
    """ISO 格式时间转 YYYY-MM-dd HH:mm:ss（UTC+8）"""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        dt_cn = dt.astimezone(timezone(timedelta(hours=8)))
        return dt_cn.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""


def _format_word_count(word_num: str) -> str:
    """字数格式化：>10000 转 x.x万"""
    if not word_num:
        return "0"
    try:
        n = int(word_num)
        if n > 10000:
            return f"{n / 10000:.1f}万"
        return str(n)
    except ValueError:
        return word_num


def _status_text(creation_status: str) -> str:
    """0 连载 1 完结 → 正常-连载 / 正常-完结"""
    if creation_status == "1":
        return "正常-完结"
    return "正常-连载"


def _roles_from_raw(raw: Any) -> str:
    """角色字段：优先解析 roles 数组，否则用 role 字符串"""
    if isinstance(raw, list):
        return ",".join(str(x) for x in raw if x)
    if isinstance(raw, str):
        try:
            arr = json.loads(raw)
            if isinstance(arr, list):
                return ",".join(str(x) for x in arr if x)
        except (json.JSONDecodeError, TypeError):
            pass
        return raw
    return ""


def _detect_book_type(data: dict[str, Any]) -> str:
    """根据详情字段判断书籍类型。"""
    book_type = data.get("book_type", "")
    genre = data.get("genre", "")
    is_ebook = data.get("is_ebook", "")
    comic_book_type = data.get("comic_book_type")
    playlet_book_id = data.get("playlet_book_id")
    schedule_mode = data.get("schedule_mode")
    album_book_order = data.get("album_book_order")

    if book_type == "1" or genre == "4":
        return "tingshu"
    if comic_book_type is not None or genre == "1":
        return "manhua"
    if playlet_book_id is not None:
        return "duanju"
    if genre == "205" and schedule_mode is not None:
        if album_book_order is not None:
            return "duanju"
        return "manju"
    if genre == "203":
        return "duanju"
    if is_ebook == "1" or genre == "0":
        return "xiaoshuo"
    return "xiaoshuo"


_BOOK_TYPE_CODE_MAP = {
    "xiaoshuo": 8,
    "tingshu": 32,
    "duanju": 4,
    "manju": 4,
    "manhua": 64,
}


def _book_type_code(book_type: str) -> int:
    return _BOOK_TYPE_CODE_MAP.get(book_type, 8)


@HandlerRegistry.register
class TutuDetailHandler(DetailBaseHandler):
    """tutu 详情处理器"""
    path = "/tutu/detail"
    name = "tutu_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "tutu 详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = kwargs.get("base_url", "").rstrip('/') + "/api/v1"
        book_id = kwargs.get("book_id", "")

        import httpx

        url = f"{base_url.rstrip('/')}/books/{book_id}"
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        d = resp.json()["data"]

        book_type = _detect_book_type(d)
        return BookDetail(
            bookType=book_type,
            bookTypeCode=_book_type_code(book_type),
            authorId=d.get("author_id", ""),
            bookId=d.get("book_id", ""),
            name=d.get("original_book_name", "") or d.get("book_name", ""),
            aliasName=d.get("book_flight_alias_name", ""),
            author=d.get("author", ""),
            status=_status_text(d.get("creation_status", "0")),
            createTime=_format_create_time(d.get("create_time", "")),
            lastUpdateTime=_format_time(d.get("last_chapter_update_time", "")),
            wordCount=_format_word_count(d.get("word_number", "")),
            category=d.get("category", "").replace("/", "，"),
            tags=d.get("tags", ""),
            roles=_roles_from_raw(d.get("roles") or d.get("role", "")),
            tones=d.get("tones", ""),
            score=d.get("score", "0"),
            readCount=d.get("sub_info", "").replace("在读", ""),
            source=d.get("source", "").split("，")[0],
            intro=d.get("abstract", ""),
            copyright=d.get("copyright_info", "").split("，")[0],
            bookReview="无",
            coverUrl=d.get("detail_page_thumb_url", "") or d.get("thumb_url", ""),
            lastChapter=d.get("last_chapter_title", ""),
        )
