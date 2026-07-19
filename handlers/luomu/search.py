from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse
from utils.fq_utils import DEFAULT_TIMEOUT, build_book_item, extract_book_data, normalize_api_base, strip_search_prefix

TAB_MAP: dict[str, str] = {
    "3": "小说",
    "2": "听书",
    "8": "漫画",
    "11": "短剧",
    "19": "漫剧",
    "13": "短篇",
    "12": "出版",
}


@HandlerRegistry.register
class LuomuSearchHandler(SearchBaseHandler):
    path = "/luomu/search"
    name = "luomu_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "page", "tab_type"]
    description = "番茄（落幕）搜索（tab_type 数字映射中文 tab）"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        query = strip_search_prefix(kwargs.get("query", ""))
        page = kwargs.get("page", "1")
        tab = TAB_MAP.get(kwargs.get("tab_type", ""), "小说")

        url = f"{base_url}/search?source=番茄&page={page}&query={query}&tab={tab}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = extract_book_data(body)
        book_list = [build_book_item(item) for item in raw_list]
        return SearchResponse(bookList=book_list)
