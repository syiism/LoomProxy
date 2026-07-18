from __future__ import annotations

from typing import Any

import httpx

from ..base.base import HandlerRegistry
from ..base.contentBase import ContentBaseHandler, ContentResponse
from ..base.exploreBase import ExploreBaseHandler, ExploreResponse
from ..base.searchBase import BookItem
from .search import build_book_item

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def _api_base(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base + "/api" if not base.endswith("/api") else base


def _build_book_item(d: dict[str, Any]) -> BookItem:
    return BookItem(
        bookId=d.get("book_id", ""),
        name=d.get("book_name", ""),
        author=d.get("author", ""),
        kind=_build_kind(d),
        wordCount=str(d.get("word_number", "")),
        lastChapter=d.get("last_chapter_title", ""),
        intro=d.get("abstract", ""),
        coverUrl=d.get("thumb_url", ""),
    )


def _build_kind(item: dict[str, Any]) -> str:
    parts = []
    gender = item.get("gender", "")
    score = item.get("score", "")
    category = item.get("category", "")
    status = item.get("creation_status", "")
    if gender:
        parts.append({"1": "男生", "2": "女生", "0": "女生"}.get(str(gender), ""))
    if score:
        parts.append(f"{score}分")
    if category:
        parts.append(category)
    if status:
        parts.append("连载" if str(status) == "1" else "完结")
    return ",".join(p for p in parts if p)


@HandlerRegistry.register
class MufanFrontHandler(ContentBaseHandler):
    path = "/mufan/front"
    name = "mufan_front"
    methods = ["GET"]
    query_params = ["base_url", "tab"]
    description = "mufan 发现页分类"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = _api_base(kwargs.get("base_url", ""))
        tab = kwargs.get("tab", "0")

        url = f"{base_url}/front?tab={tab}"
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return ContentResponse(contentType="categories", data=data)


@HandlerRegistry.register
class MufanLandingHandler(ExploreBaseHandler):
    path = "/mufan/landing"
    name = "mufan_landing"
    methods = ["GET"]
    query_params = [
        "base_url", "category_id", "offset",
        "genre_type", "gender", "word_number", "book_status", "sort_by",
    ]
    description = "mufan 分类落地页书籍列表"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _api_base(kwargs.get("base_url", ""))
        category_id = kwargs.get("category_id", "")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/landing?category_id={category_id}&offset={offset}"
        for param in ("genre_type", "gender", "word_number", "book_status", "sort_by"):
            val = kwargs.get(param)
            if val:
                url += f"&{param}={val}"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        book_info = resp.json().get("data", {}).get("book_info", [])
        book_list = [_build_book_item(item) for item in book_info if item.get("book_id")]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class MufanRecommendHandler(ExploreBaseHandler):
    path = "/mufan/recommend"
    name = "mufan_recommend"
    methods = ["GET"]
    query_params = ["base_url", "tab_type", "offset"]
    description = "mufan 首页推荐"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _api_base(kwargs.get("base_url", ""))
        tab_type = kwargs.get("tab_type", "2")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/recommend/homepage?tab_type={tab_type}&offset={offset}"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", {}).get("book_info", [])
        book_list = [build_book_item(item) for item in raw_list if item.get("book_id")]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class MufanRankHandler(ExploreBaseHandler):
    path = "/mufan/rank"
    name = "mufan_rank"
    methods = ["GET"]
    query_params = ["base_url", "genre_tab", "algo_type", "offset", "limit"]
    description = "mufan 排行榜"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _api_base(kwargs.get("base_url", ""))
        genre_tab = kwargs.get("genre_tab", "2")
        algo_type = kwargs.get("algo_type", "101")
        offset = kwargs.get("offset", "0")
        limit = kwargs.get("limit", "10")

        url = f"{base_url}/bookmall/cell/change?genre_tab={genre_tab}&algo_type={algo_type}&offset={offset}&limit={limit}"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", {}).get("book_info", [])
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)
