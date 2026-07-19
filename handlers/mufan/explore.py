from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse
from base.exploreBase import ExploreBaseHandler, ExploreResponse
from utils.fq_utils import DEFAULT_TIMEOUT, build_book_item, normalize_api_base


@HandlerRegistry.register
class MufanFrontHandler(ContentBaseHandler):
    path = "/mufan/front"
    name = "mufan_front"
    methods = ["GET"]
    query_params = ["base_url", "tab"]
    description = "番茄（沐凡）发现页分类"

    async def handle(self, **kwargs: Any) -> ContentResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""))
        tab = kwargs.get("tab", "0")

        url = f"{base_url}/front?tab={tab}"
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
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
    description = "番茄（沐凡）分类落地页书籍列表"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""))
        category_id = kwargs.get("category_id", "")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/landing?category_id={category_id}&offset={offset}"
        for param in ("genre_type", "gender", "word_number", "book_status", "sort_by"):
            val = kwargs.get(param)
            if val:
                url += f"&{param}={val}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        book_info = resp.json().get("data", {}).get("book_info", [])
        book_list = [build_book_item(item) for item in book_info if item.get("book_id")]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class MufanRecommendHandler(ExploreBaseHandler):
    path = "/mufan/recommend"
    name = "mufan_recommend"
    methods = ["GET"]
    query_params = ["base_url", "tab_type", "offset"]
    description = "番茄（沐凡）首页推荐"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""))
        tab_type = kwargs.get("tab_type", "2")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/recommend/homepage?tab_type={tab_type}&offset={offset}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
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
    description = "番茄（沐凡）排行榜"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""))
        genre_tab = kwargs.get("genre_tab", "2")
        algo_type = kwargs.get("algo_type", "101")
        offset = kwargs.get("offset", "0")
        limit = kwargs.get("limit", "10")

        url = f"{base_url}/bookmall/cell/change?genre_tab={genre_tab}&algo_type={algo_type}&offset={offset}&limit={limit}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", {}).get("book_info", [])
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)
