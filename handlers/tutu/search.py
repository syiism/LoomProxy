from typing import Any

import httpx

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse
from utils.fq_utils import DEFAULT_TIMEOUT, build_book_item, normalize_api_base, strip_search_prefix


def parse_tab_item(tab_item: Any) -> list[dict[str, Any]]:
    """递归解析 searchTabs，收集 book_data / video_data / abstract 节点。"""
    data_list: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if not node or not isinstance(node, (dict, list)):
            return

        if isinstance(node, dict):
            book_data = node.get("book_data")
            if isinstance(book_data, list) and book_data:
                for b in book_data:
                    if b and isinstance(b, dict):
                        data_list.append(b)

            video_data = node.get("video_data")
            if isinstance(video_data, list) and video_data:
                for v in video_data:
                    if v and isinstance(v, dict):
                        data_list.append(v)

            if "abstract" in node:
                data_list.append(node)

            node_data = node.get("data")
            if isinstance(node_data, list):
                for item in node_data:
                    walk(item)

        if isinstance(node, list):
            for item in node:
                walk(item)

    walk(tab_item)
    return data_list


@HandlerRegistry.register
class TutuSearchHandler(SearchBaseHandler):
    """tutu 搜索处理器"""
    path = "/tutu/search"
    name = "tutu_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "offset", "count", "tab_type"]
    description = "番茄（兔兔）搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = kwargs.get("base_url", "").rstrip('/')
        query = strip_search_prefix(kwargs.get("query", ""))
        offset = kwargs.get("offset", "")
        count = kwargs.get("count", "")
        tab_type = kwargs.get("tab_type", "")

        api_base = normalize_api_base(base_url, "/api/v1")

        if query.isdigit() and len(query) > 5:
            url = f"{api_base}/books/{query}"
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
                resp = await self.fetch(client, url)
            resp.raise_for_status()
            detail_data = resp.json().get("data", {})
            item = build_book_item(detail_data)
            return SearchResponse(bookList=[item])

        url = f"{api_base}/search?query={query}&offset={offset}&count={count}&tab_type={tab_type}"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            data = await self.fetch(client, url)
        data.raise_for_status()
        data = data.json()

        search_tabs = data["search_tabs"]
        raw_list = parse_tab_item(search_tabs)
        book_list = [build_book_item(item) for item in raw_list]

        return SearchResponse(bookList=book_list)
