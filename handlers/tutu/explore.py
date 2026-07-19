from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.exploreBase import ExploreBaseHandler, ExploreResponse
from utils.fq_utils import DEFAULT_TIMEOUT, build_book_item, extract_book_data, normalize_api_base


@HandlerRegistry.register
class TutuRecommendHandler(ExploreBaseHandler):
    path = "/tutu/recommend"
    name = "tutu_recommend"
    methods = ["GET"]
    query_params = ["base_url", "tab_type", "offset"]
    description = "番茄（兔兔）首页推荐"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        tab_type = kwargs.get("tab_type", "2")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/recommend/homepage?tab_type={tab_type}&offset={offset}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = extract_book_data(data)
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class TutuRankHandler(ExploreBaseHandler):
    path = "/tutu/rank"
    name = "tutu_rank"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "offset", "genre_tab", "rank_sub_info_id", "algo_type"]
    description = "番茄（兔兔）排行榜"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "7098235271900037133")
        offset = kwargs.get("offset", "0")
        genre_tab = kwargs.get("genre_tab", "2")
        rank_sub_info_id = kwargs.get("rank_sub_info_id", "2")
        algo_type = kwargs.get("algo_type", "101")

        url = (
            f"{base_url}/rank/{book_id}"
            f"?offset={offset}&genre_tab={genre_tab}"
            f"&rank_sub_info_id={rank_sub_info_id}&algo_type={algo_type}"
        )

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        data = resp.json()

        cells = data.get("data", {}).get("cell_view", {}).get("cell_data", [])
        raw_list = extract_book_data(cells)
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class TutuRelatedHandler(ExploreBaseHandler):
    path = "/tutu/related"
    name = "tutu_related"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "番茄（兔兔）相关作品"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/books/{book_id}/related"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = extract_book_data(data)
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class TutuAuthorHandler(ExploreBaseHandler):
    path = "/tutu/author"
    name = "tutu_author"
    methods = ["GET"]
    query_params = ["base_url", "author_id"]
    description = "番茄（兔兔）作者作品"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        author_id = kwargs.get("author_id", "")

        url = f"{base_url}/authors/{author_id}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = data.get("data", {}).get("author_book_info", [])
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)
