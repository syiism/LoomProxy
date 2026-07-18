from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse
from utils.fq_utils import DEFAULT_TIMEOUT, build_book_item, normalize_api_base, strip_search_prefix


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


@HandlerRegistry.register
class MufanSearchHandler(SearchBaseHandler):
    path = "/mufan/search"
    name = "mufan_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "offset", "count", "tab_type", "search_type"]
    description = "mufan 搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = kwargs.get("base_url", "").rstrip("/")
        api_base = normalize_api_base(base_url, "/api")
        query = strip_search_prefix(kwargs.get("query", ""))
        offset = kwargs.get("offset", "")
        tab_type = kwargs.get("tab_type", "")
        search_type = kwargs.get("search_type", "")
        count = kwargs.get("count", 0)

        if query.isdigit() and len(query) > 5:
            url = f"{api_base}/detail?book_id={query}"
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            item = build_book_item(resp.json().get("data", {}))
            return SearchResponse(bookList=[item])

        url = f"{api_base}/search?key={quote(query)}&tab_type={tab_type}&offset={offset}"
        if count:
            url += f"&count={count}"
        if search_type:
            url += f"&search_type={search_type}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()
        data = (body or {}).get("data") or {}
        tabs = data.get("search_tabs", [])
        raw_list = extract_book_data(tabs)
        book_list = [build_book_item(item) for item in raw_list]
        return SearchResponse(bookList=book_list)
