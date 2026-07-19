from typing import Any

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse
from utils.fq_utils import build_book_item, normalize_api_base


def parse_search_results(data: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if not node or not isinstance(node, (dict, list)):
            return
        if isinstance(node, dict):
            book_data = node.get("book_data")
            if isinstance(book_data, list):
                for b in book_data:
                    if b and isinstance(b, dict) and b.get("book_id"):
                        items.append(b)
            video_data = node.get("video_data")
            if isinstance(video_data, list):
                for v in video_data:
                    if v and isinstance(v, dict) and v.get("series_id"):
                        items.append(v)
            for key in ("search_tabs", "data", "results"):
                child = node.get(key)
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return items


@HandlerRegistry.register
class XinghaiSearchHandler(SearchBaseHandler):
    path = "/fq_xinghai/search"
    name = "fq_xinghai_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "offset", "tab_type"]
    description = "星海搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        query = kwargs.get("query", "")
        offset = kwargs.get("offset", "0")
        tab_type = kwargs.get("tab_type", "1")

        url = f"{base_url}/search?query={query}&offset={offset}&filter=none&tab_type={tab_type}"

        resp = await self.fetch(url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = parse_search_results(data)
        book_list = [build_book_item(item) for item in raw_list]

        return SearchResponse(bookList=book_list)
