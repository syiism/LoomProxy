from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse
from utils.fq_utils import DEFAULT_TIMEOUT, build_book_item, extract_book_data, normalize_api_base, strip_search_prefix


@HandlerRegistry.register
class JingluoSearchHandler(SearchBaseHandler):
    path = "/jingluo/search"
    name = "jingluo_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "tab_type", "offset"]
    description = "番茄（鲸落）搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "")
        query = strip_search_prefix(kwargs.get("query", ""))
        tab_type = kwargs.get("tab_type", "0")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/search?query={query}&tab_type={tab_type}&offset={offset}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await self.fetch(client, url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = extract_book_data(body)
        book_list = [build_book_item(item) for item in raw_list]
        return SearchResponse(bookList=book_list)
