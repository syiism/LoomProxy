from __future__ import annotations

from typing import Any

from base.base import HandlerRegistry
from base.searchBase import BookItem, SearchBaseHandler, SearchResponse
from utils.fq_utils import normalize_api_base


def build_kind(item: dict[str, Any]) -> str:
    parts = []
    status = item.get("status", 0)
    parts.append("完结" if status == 1 else "连载")
    tags = item.get("tags", "")
    if tags:
        parts.append(tags)
    return ",".join(parts)


def build_book_item(item: dict[str, Any]) -> BookItem:
    return BookItem(
        bookId=str(item.get("bid", "")),
        name=item.get("title", ""),
        author=item.get("author", ""),
        kind=build_kind(item),
        wordCount=str(item.get("words", 0)),
        lastChapter=item.get("first_chapter", ""),
        intro=item.get("desc", ""),
        coverUrl=item.get("cover", ""),
    )


@HandlerRegistry.register
class SqLuomuSearchHandler(SearchBaseHandler):
    path = "/sq_luomu/search"
    name = "sq_luomu_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "page"]
    description = "书旗（落幕）搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        base_url = normalize_api_base(kwargs.get("base_url", ""), "/api")
        query = kwargs.get("query", "")
        page = kwargs.get("page", "1")

        url = f"{base_url}/search?source=书旗&page={page}&query={query}&tab=小说"

        resp = await self.fetch(url)
        resp.raise_for_status()
        body = resp.json()

        raw_list = body.get("data", [])
        book_list = [build_book_item(item) for item in raw_list if item.get("bid")]
        return SearchResponse(bookList=book_list)
