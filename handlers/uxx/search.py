from typing import Any

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse

from utils.uxx_utils import MOBILE_UA, parse_list_html


@HandlerRegistry.register
class UxxSearchHandler(SearchBaseHandler):
    path = "/uxx/search"
    name = "uxx_search"
    methods = ["GET"]
    query_params = ["query", "page"]
    description = "海阔视界搜索"
    auth_required = False

    async def handle(self, **kwargs: Any) -> SearchResponse:
        query = kwargs.get("query", "").strip()
        page = kwargs.get("page", "1")
        
        url = f"https://www.uxx001.com/?c=search&wd={query}&sort=addtime&order=desc&page={page}"
        
        resp = await self.fetch(url, headers={"User-Agent": MOBILE_UA})
        resp.raise_for_status()
        html = resp.text
        
        book_list = parse_list_html(html)
        
        return SearchResponse(bookList=book_list)