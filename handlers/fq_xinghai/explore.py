from __future__ import annotations

from typing import Any

from base.base import HandlerRegistry
from base.exploreBase import ExploreBaseHandler, ExploreResponse
from utils.fq_utils import build_book_item, normalize_api_base


def _extract_cell_entries(cell: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not isinstance(cell, dict):
        return items
    for entry in cell.get("book_data", []):
        if isinstance(entry, dict) and entry.get("book_id"):
            items.append(entry)
    for entry in cell.get("video_data", []):
        if isinstance(entry, dict) and entry.get("series_id"):
            items.append(entry)
    if not items:
        for inner in cell.get("cell_data", []):
            items.extend(_extract_cell_entries(inner))
    return items


def parse_recommend_cells(data: dict[str, Any], tab_type: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    tab_item = data.get("data", {}).get("tab_item", [])
    for tab in tab_item:
        if str(tab.get("tab_type")) != tab_type:
            continue
        for cell in tab.get("cell_data", []):
            items.extend(_extract_cell_entries(cell))
    return items


@HandlerRegistry.register
class XinghaiRecommendHandler(ExploreBaseHandler):
    path = "/fq_xinghai/recommend"
    name = "fq_xinghai_recommend"
    methods = ["GET"]
    query_params = ["base_url", "tab_type", "offset"]
    description = "星海首页推荐"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api/v1")
        tab_type = kwargs.get("tab_type", "2")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/recommend/homepage?offset={offset}&filter=none&tab_type={tab_type}"

        resp = await self.fetch(url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = parse_recommend_cells(data, tab_type)
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class XinghaiRankHandler(ExploreBaseHandler):
    path = "/fq_xinghai/rank"
    name = "fq_xinghai_rank"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "offset", "genre_tab", "rank_sub_info_id", "algo_type"]
    description = "星海排行榜"

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
            f"&rank_sub_info_id={rank_sub_info_id}&algo_type={algo_type}&filter=none"
        )

        resp = await self.fetch(url)
        resp.raise_for_status()
        data = resp.json()

        cells = data.get("data", {}).get("cell_view", {}).get("cell_data", [])
        raw_list = extract_book_data(cells)
        book_list = [build_book_item(item) for item in raw_list]
        return ExploreResponse(bookList=book_list)
