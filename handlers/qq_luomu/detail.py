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


def _format_word_count(word_num: Any) -> str:
    if not word_num:
        return "0"
    try:
        n = int(word_num)
        return f"{n / 10000:.1f}万" if n > 10000 else str(n)
    except ValueError:
        return str(word_num)


@HandlerRegistry.register
class QQLuomuDetailHandler(DetailBaseHandler):
    path = "/qq_luomu/detail"
    name = "qq_luomu_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "qq阅读（落幕）详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/detail?source=QQ阅读&book_id={book_id}&tab=小说"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        d = resp.json().get("data", {})

        return BookDetail(
            bookType="xiaoshuo",
            bookTypeCode=8,
            authorId=str(d.get("authorid", "")),
            bookId=str(d.get("id", "")),
            name=d.get("title", ""),
            aliasName="",
            author=d.get("author", ""),
            status="正常-完结" if d.get("isfinished") == 1 else "正常-连载",
            createTime=d.get("createTime", ""),
            lastUpdateTime=_format_time(d.get("updateDate", "")),
            wordCount=_format_word_count(d.get("wordscount", 0)),
            category=d.get("categoryName", ""),
            tags="",
            roles="",
            tones="",
            score=str(d.get("bookScore", "0")),
            readCount="",
            source="QQ阅读",
            intro=d.get("intro", ""),
            copyright="",
            bookReview="无",
            coverUrl=d.get("coverUrl", ""),
            lastChapter=d.get("lastupdatechaptername", ""),
        )
