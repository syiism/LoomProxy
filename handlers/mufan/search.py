from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import httpx

from ..base.base import HandlerRegistry
from ..base.searchBase import BookItem, SearchBaseHandler, SearchResponse

GENDER_MAP = {"0": "女生", "1": "男生", "2": "出版"}
CREATION_STATUS_MAP = {"0": "完结", "1": "连载", "-1": "未知"}
TZ_SHANGHAI = timezone(timedelta(hours=8))
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def _strip_search_prefix(query: str) -> str:
    """去除 Legado 书源前缀 +1/+3/+11/+19 等（URL 中 + 可能被解码为空格）"""
    import re
    return re.sub(r"^[\s+]+\d+\s*", "", query)


def build_kind(item: dict[str, Any]) -> str:
    gender = GENDER_MAP.get(str(item.get("gender", "")), "未知")
    score = item.get("score", "") + "分"
    category = item.get("category", "")
    status = CREATION_STATUS_MAP.get(str(item.get("creation_status", "")), "未知")
    ts = item.get("last_publish_time") or item.get("last_chapter_update_time", "")
    last_update = ""
    if ts:
        try:
            last_update = datetime.fromtimestamp(int(ts), tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return ",".join([gender, str(score), str(category), status, last_update])


def extract_book_data(tabs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for tab in tabs:
        cells = tab.get("data") or []
        for cell in cells:
            book_data = cell.get("book_data") or []
            for bd in book_data:
                if bd and isinstance(bd, dict) and bd.get("book_id"):
                    items.append(bd)
            video_data = cell.get("video_data") or []
            for vd in video_data:
                if vd and isinstance(vd, dict) and vd.get("series_id"):
                    items.append(vd)
    return items


def build_video_kind(item: dict[str, Any]) -> str:
    rec_text = item.get("rec_text", "")
    score = item.get("score", "") + "分"
    sub_title = item.get("sub_title", "").replace("·", ",")
    return ",".join([rec_text, score, sub_title])


def build_book_item(item: dict[str, Any]) -> BookItem:
    if "book_name" in item:
        return BookItem(
            bookId=item.get("book_id", ""),
            name=item.get("book_name", ""),
            author=item.get("author", ""),
            kind=build_kind(item),
            wordCount=str(item.get("word_number", "")),
            lastChapter=item.get("last_chapter_title", ""),
            intro=item.get("abstract", ""),
            coverUrl=item.get("thumb_url", ""),
        )
    return BookItem(
        bookId=item.get("series_id", ""),
        name=item.get("title", ""),
        author=item.get("copyright", ""),
        kind=build_video_kind(item),
        wordCount="",
        lastChapter="",
        intro=item.get("video_detail", {}).get("series_intro", ""),
        coverUrl=item.get("cover", ""),
    )


@HandlerRegistry.register
class MufanSearchHandler(SearchBaseHandler):
    path = "/mufan/search"
    name = "mufan_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "offset", "count", "tab_type", "search_type"]
    description = "mufan 搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = kwargs.get("base_url", "").rstrip("/")
        api_base = base_url + "/api" if not base_url.endswith("/api") else base_url
        query = _strip_search_prefix(kwargs.get("query", ""))
        offset = kwargs.get("offset", "")
        tab_type = kwargs.get("tab_type", "")
        search_type = kwargs.get("search_type", "")
        count = kwargs.get("count", 0)

        if query.isdigit() and len(query) > 5:
            url = f"{api_base}/detail?book_id={query}"
            async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            item = build_book_item(resp.json().get("data", {}))
            return SearchResponse(bookList=[item])

        url = f"{api_base}/search?key={quote(query)}&tab_type={tab_type}&offset={offset}"
        if count:
            url += f"&count={count}"
        if search_type:
            url += f"&search_type={search_type}"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()
        data = (body or {}).get("data") or {}
        tabs = data.get("search_tabs", [])
        raw_list = extract_book_data(tabs)
        book_list = [build_book_item(item) for item in raw_list]
        return SearchResponse(bookList=book_list)
