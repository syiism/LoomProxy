from typing import Any

from base.base import HandlerRegistry
from base.exploreBase import ExploreBaseHandler, ExploreResponse

from utils.uxx_utils import MOBILE_UA, parse_list_html


@HandlerRegistry.register
class UxxRecommendHandler(ExploreBaseHandler):
    path = "/uxx/recommend"
    name = "uxx_recommend"
    methods = ["GET"]
    query_params = ["tab_type", "page"]
    description = "海阔视界首页推荐"
    auth_required = False

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        tab_type = kwargs.get("tab_type", "1")
        page = kwargs.get("page", "1")
        
        url = f"https://www.uxx001.com/type/{tab_type}/{page}.html"
        
        resp = await self.fetch(url, headers={"User-Agent": MOBILE_UA})
        resp.raise_for_status()
        html = resp.text
        
        book_list = parse_list_html(html)
        
        return ExploreResponse(bookList=book_list)