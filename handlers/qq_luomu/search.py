from __future__ import annotations

from typing import Any

import httpx

from base.base import HandlerRegistry
from base.searchBase import BookItem, SearchBaseHandler, SearchResponse
from utils.fq_utils import DEFAULT_TIMEOUT, normalize_api_base


def build_kind(item: dict[str, Any]) -> str:
    parts = []
    if item.get("finished"):
        parts.append("完结")
    else:
        parts.append("连载")
    if item.get("totalChapters"):
        parts.append(f"{item['totalChapters']}章")
    return ",".join(parts)


def build_book_item(item: dict[str, Any]) -> BookItem:
    return BookItem(
        bookId=str(item.get("id", "")),
        name=item.get("title", ""),
        author=item.get("author", ""),
        kind=build_kind(item),
        wordCount=str(item.get("totalWords", 0)),
        lastChapter="",
        intro=item.get("intro", ""),
        coverUrl=item.get("cover", ""),
    )


@HandlerRegistry.register
class QQLuomuSearchHandler(SearchBaseHandler):
    path = "/qq_luomu/search"
    name = "qq_luomu_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "page"]
    description = "qq阅读（落幕）搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        query = kwargs.get("query", "")
        page = kwargs.get("page", "1")

        url = f"{base_url}/search?source=QQ阅读&page={page}&query={query}&tab=小说"

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url)
        resp.raise_for_status()
        body = resp.json()

        books = body.get("data", {}).get("books", [])
        book_list = [build_book_item(item) for item in books if item.get("id")]
        return SearchResponse(bookList=book_list)
