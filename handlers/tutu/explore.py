from __future__ import annotations

from typing import Any

import httpx

from ..base.base import HandlerRegistry
from ..base.exploreBase import ExploreBaseHandler, ExploreResponse
from ..base.searchBase import BookItem
from .search import build_book_item

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


def _normalize_base(base_url: str) -> str:
    """确保 base_url 以正确的 API 前缀结尾（兼容带或不带 /api/v1）"""
    base = base_url.rstrip('/')
    if base.endswith("/api/v1"):
        return base
    return base + "/api/v1"


def _extract_book_data(obj: Any, depth: int = 0, max_depth: int = 9) -> list[dict[str, Any]]:
    """递归提取嵌套结构中所有的 book_data / video_data 列表项"""
    items: list[dict[str, Any]] = []
    if depth > max_depth:
        return items
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "book_data" and isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and item.get("book_id"):
                        items.append(item)
            elif k == "video_data" and isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and item.get("series_id"):
                        items.append(item)
            else:
                items.extend(_extract_book_data(v, depth + 1, max_depth))
    elif isinstance(obj, list):
        for item in obj:
            items.extend(_extract_book_data(item, depth + 1, max_depth))
    return items


def _normalize_video_item(item: dict[str, Any]) -> dict[str, Any]:
    """补齐 video_data 项缺少的 rec_text / sub_title 字段"""
    if "book_name" in item or item.get("rec_text"):
        return item

    # 方式1：从 card_tips 解析（rank 接口）
    card_tips = item.get("card_tips", "")
    if card_tips:
        parts = card_tips.split("·")
        if len(parts) >= 3:
            item.setdefault("rec_text", parts[-1])
            item.setdefault("sub_title", "·".join(parts[:-1]))
        elif len(parts) == 2:
            item.setdefault("rec_text", parts[-1])
            item.setdefault("sub_title", parts[0])
        return item

    # 方式2：从 sub_title_list / secondary_info_list 拼接（related 接口）
    stl = item.get("sub_title_list", [])
    if stl:
        item.setdefault("sub_title", "·".join(s.get("content", "") for s in stl))
    sil = item.get("secondary_info_list", [])
    if sil:
        item.setdefault("rec_text", "·".join(s.get("content", "") for s in sil))

    return item


def _build_book_list(raw_list: list[dict[str, Any]], base_url: str) -> list[BookItem]:
    """将原始 book_data / video_data 列表转换为 BookItem 列表"""
    raw_list = [_normalize_video_item(item) for item in raw_list]
    return [build_book_item(item, base_url) for item in raw_list]


@HandlerRegistry.register
class TutuRecommendHandler(ExploreBaseHandler):
    """tutu 首页推荐处理器"""
    path = "/tutu/recommend"
    name = "tutu_recommend"
    methods = ["GET"]
    query_params = ["base_url", "tab_type", "offset"]
    description = "tutu 首页推荐"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _normalize_base(kwargs.get("base_url", ""))
        tab_type = kwargs.get("tab_type", "2")
        offset = kwargs.get("offset", "0")

        url = f"{base_url}/recommend/homepage?tab_type={tab_type}&offset={offset}"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = _extract_book_data(data)
        book_list = _build_book_list(raw_list, base_url)
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class TutuRankHandler(ExploreBaseHandler):
    """tutu 排行榜处理器"""
    path = "/tutu/rank"
    name = "tutu_rank"
    methods = ["GET"]
    query_params = ["base_url", "book_id", "offset", "genre_tab", "rank_sub_info_id", "algo_type"]
    description = "tutu 排行榜"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _normalize_base(kwargs.get("base_url", ""))
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

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        cells = data.get("data", {}).get("cell_view", {}).get("cell_data", [])
        raw_list = _extract_book_data(cells)
        book_list = _build_book_list(raw_list, base_url)
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class TutuRelatedHandler(ExploreBaseHandler):
    """tutu 相关作品"""
    path = "/tutu/related"
    name = "tutu_related"
    methods = ["GET"]
    query_params = ["base_url", "book_id"]
    description = "tutu 相关作品"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _normalize_base(kwargs.get("base_url", ""))
        book_id = kwargs.get("book_id", "")

        url = f"{base_url}/books/{book_id}/related"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = _extract_book_data(data)
        book_list = _build_book_list(raw_list, base_url)
        return ExploreResponse(bookList=book_list)


@HandlerRegistry.register
class TutuAuthorHandler(ExploreBaseHandler):
    """tutu 作者作品"""
    path = "/tutu/author"
    name = "tutu_author"
    methods = ["GET"]
    query_params = ["base_url", "author_id"]
    description = "tutu 作者作品"

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        base_url = _normalize_base(kwargs.get("base_url", ""))
        author_id = kwargs.get("author_id", "")

        url = f"{base_url}/authors/{author_id}"

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

        raw_list = data.get("data", {}).get("author_book_info", [])
        book_list = _build_book_list(raw_list, base_url)
        return ExploreResponse(bookList=book_list)
