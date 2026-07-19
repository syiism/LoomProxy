from __future__ import annotations

from datetime import datetime
from typing import Any

from base.base import HandlerRegistry
from base.detailBase import BookDetail, DetailBaseHandler
from utils.fq_utils import TZ_SHANGHAI, normalize_api_base


def _format_word_count(wc: Any) -> str:
    if not wc:
        return "0"
    try:
        n = int(float(str(wc)) * 10000) if "." in str(wc) else int(str(wc))
        return f"{n / 10000:.1f}万" if n > 10000 else str(n)
    except (ValueError, TypeError):
        return str(wc)


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


@HandlerRegistry.register
class SqLuomuDetailHandler(DetailBaseHandler):
    path = "/sq_luomu/detail"
    name = "sq_luomu_detail"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "书旗（落幕）详情"

    async def handle(self, **kwargs: Any) -> BookDetail:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/detail?source=书旗&book_id={book_id}&tab=小说"
        resp = await self.fetch(url)
        resp.raise_for_status()
        d = resp.json().get("data", {})

        chapter_list = d.get("chapterList", [])

        return BookDetail(
            bookType="xiaoshuo",
            bookTypeCode=8,
            authorId=str(d.get("authorId", "")),
            bookId=str(d.get("bookId", "")),
            name=d.get("bookName", ""),
            aliasName="",
            author=d.get("authorName", ""),
            status="正常-完结" if d.get("state") == 1 else "正常-连载",
            createTime="",
            lastUpdateTime=_format_time(d.get("lastInsTime", "")),
            wordCount=_format_word_count(d.get("realTimeWordCount", d.get("wordCount", "0"))),
            category="",
            tags="",
            roles="",
            tones="",
            score="",
            readCount="",
            source="书旗",
            intro=d.get("intro", ""),
            copyright=d.get("cpName", "无"),
            bookReview="无",
            coverUrl=d.get("imgUrl", ""),
            lastChapter=chapter_list[-1]["volumeList"][-1]["chapterName"] if chapter_list and chapter_list[-1].get("volumeList") else "",
        )
