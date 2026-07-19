from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.searchBase import BookItem, SearchBaseHandler, SearchResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base


def build_kind(item: dict[str, Any]) -> str:
    parts = []
    status = item.get("is_over", "0")
    parts.append("完结" if status == "1" else "连载")
    score = item.get("score", "")
    if score:
        parts.append(f"{score}分")
    sub = item.get("sub_title", "")
    if sub:
        parts.append(sub)
    return ",".join(parts)


def build_book_item(item: dict[str, Any]) -> BookItem:
    return BookItem(
        bookId=str(item.get("id", "")),
        name=item.get("title", ""),
        author=item.get("author", ""),
        kind=build_kind(item),
        wordCount=item.get("words_num", "0"),
        lastChapter="",
        intro=item.get("intro", ""),
        coverUrl=item.get("image_link", ""),
    )


@HandlerRegistry.register
class QmLuomuSearchHandler(SearchBaseHandler):
    path = "/qm_luomu/search"
    name = "qm_luomu_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "page"]
    description = "七猫（落幕）搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        query = kwargs.get("query", "")
        page = kwargs.get("page", "1")

        url = f"{base_url}/search?source=七猫&page={page}&query={query}&tab=小说"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", {}).get("data", {}).get("books", [])
        book_list = [build_book_item(item) for item in raw_list if item.get("id")]
        return SearchResponse(bookList=book_list)
