from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from base.base import HandlerRegistry
from base.detailBase import BookDetail, DetailBaseHandler
from utils.fq_utils import DEFAULT_TIMEOUT, TZ_SHANGHAI, normalize_api_base


def _format_time(ts_val: Any) -> str:
    if not ts_val:
        return ""
    try:
        ts = int(ts_val)
        if ts > 1e12:
            ts //= 1000
        dt = datetime.fromtimestamp(ts, tz=TZ_SHANGHAI)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return str(ts_val)


def _extract_score(attr: Any) -> str:
    if isinstance(attr, dict):
        for item in attr.get("extra_info_list", []):
            if item.get("type") == "1":
                return item.get("value", "0")
    return "0"


def _extract_read_count(attr: Any) -> str:
    if isinstance(attr, dict):
        for item in attr.get("extra_info_list", []):
            if item.get("unit") == "人":
                return item.get("value", "")
    return ""


@HandlerRegistry.register
class QmLuomuDetailHandler(DetailBaseHandler):
    path = "/qm_luomu/detail"
    name = "qm_luomu_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "七猫（落幕）详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/detail?source=七猫&book_id={book_id}&tab=小说"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        d = resp.json().get("data", {})

        attr = d.get("attribute", {})

        return BookDetail(
            bookType="xiaoshuo",
            bookTypeCode=8,
            authorId=d.get("author_id", ""),
            bookId=str(d.get("id", "")),
            name=d.get("title", ""),
            aliasName=d.get("alias_title", ""),
            author=d.get("author", ""),
            status="正常-完结" if d.get("is_over") == "1" else "正常-连载",
            createTime="",
            lastUpdateTime=_format_time(d.get("update_time", "")),
            wordCount=d.get("words_num", "0"),
            category=d.get("category1_name", ""),
            tags=",".join(t.get("title", "") for t in d.get("book_tag_list", []) if isinstance(t, dict)),
            roles=d.get("characters", ""),
            tones="",
            score=_extract_score(attr),
            readCount=_extract_read_count(attr),
            source="七猫",
            intro=d.get("intro", ""),
            copyright="",
            bookReview="无",
            coverUrl=d.get("image_link", ""),
            lastChapter=d.get("latest_chapter_title", ""),
        )
