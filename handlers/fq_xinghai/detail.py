from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any

from base.base import HandlerRegistry
from base.detailBase import BookDetail, DetailBaseHandler
from utils.fq_utils import _detect_book_type, book_type_code, normalize_api_base


def _format_time(ts_str: str) -> str:
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
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        dt_cn = dt.astimezone(timezone(timedelta(hours=8)))
        return dt_cn.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""


def _format_word_count(word_num: str) -> str:
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
    if creation_status == "1":
        return "正常-完结"
    return "正常-连载"


def _roles_from_raw(raw: Any) -> str:
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


@HandlerRegistry.register
class XinghaiDetailHandler(DetailBaseHandler):
    path = "/fq_xinghai/detail"
    name = "fq_xinghai_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "星海详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url.rstrip('/')}/books/{book_id}?filter=none&source=detail"

        resp = await self.fetch(url)
        resp.raise_for_status()
        d = resp.json()["data"]

        book_type = _detect_book_type(d)
        return BookDetail(
            bookType=book_type,
            bookTypeCode=book_type_code(book_type),
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
