from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from ..base.base import HandlerRegistry
from ..base.detailBase import BookDetail, DetailBaseHandler

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
TZ_SHANGHAI = timezone(timedelta(hours=8))


def _format_time(ts_str: str) -> str:
    if not ts_str:
        return ""
    try:
        ts = int(ts_str)
        if ts > 1e12:
            ts //= 1000
        dt = datetime.fromtimestamp(ts, tz=TZ_SHANGHAI)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return ""


def _format_create_time(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.astimezone(TZ_SHANGHAI).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""


def _format_word_count(word_num: str) -> str:
    if not word_num:
        return "0"
    try:
        n = int(word_num)
        return f"{n / 10000:.1f}万" if n > 10000 else str(n)
    except ValueError:
        return word_num


def _status_text(creation_status: str) -> str:
    return "正常-完结" if creation_status == "1" else "正常-连载"


def _detect_book_type(data: dict[str, Any]) -> str:
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
        return "duanju" if album_book_order is not None else "manju"
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
class MufanDetailHandler(DetailBaseHandler):
    path = "/mufan/detail"
    name = "mufan_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "mufan 详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = kwargs.get("base_url", "").rstrip("/")
        api_base = base_url + "/api" if not base_url.endswith("/api") else base_url
        book_id = kwargs.get("book_id", "")

        url = f"{api_base}/detail?book_id={book_id}"
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        d = resp.json().get("data", {})

        book_type = _detect_book_type(d)
        return BookDetail(
            bookType=book_type,
            bookTypeCode=_book_type_code(book_type),
            authorId=d.get("author_id", ""),
            bookId=d.get("book_id", ""),
            name=d.get("original_book_name", "") or d.get("book_name", ""),
            aliasName=d.get("alias_name", "") or d.get("book_flight_alias_name", ""),
            author=d.get("author", ""),
            status=_status_text(d.get("creation_status", "0")),
            createTime=_format_create_time(d.get("create_time", "")),
            lastUpdateTime=_format_time(d.get("last_chapter_update_time", "") or d.get("last_publish_time", "")),
            wordCount=_format_word_count(d.get("word_number", "")),
            category=d.get("category", "").replace("/", "，"),
            tags=d.get("tags", ""),
            roles=d.get("role", ""),
            tones=d.get("tones", ""),
            score=d.get("score", "0"),
            readCount=d.get("sub_info", "").replace("在读", ""),
            source=d.get("source", "").split("，")[0],
            intro=d.get("abstract", ""),
            copyright=d.get("copyright_info", "").split("，")[0],
            bookReview="无",
            coverUrl=d.get("thumb_url", ""),
            lastChapter=d.get("last_chapter_title", ""),
        )
