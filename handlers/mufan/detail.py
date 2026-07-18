from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from base.base import HandlerRegistry
from base.detailBase import BookDetail, DetailBaseHandler
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, _detect_book_type, book_type_code, normalize_api_base


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



@HandlerRegistry.register
class MufanDetailHandler(DetailBaseHandler):
    path = "/mufan/detail"
    name = "mufan_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "mufan 详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = kwargs.get("base_url", "").rstrip("/")
        api_base = normalize_api_base(base_url, "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{api_base}/detail?book_id={book_id}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        d = resp.json().get("data", {})

        book_type = _detect_book_type(d)
        return BookDetail(
            bookType=book_type,
            bookTypeCode=book_type_code(book_type),
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
