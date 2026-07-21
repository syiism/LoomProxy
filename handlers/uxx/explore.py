from typing import Any

from base.base import HandlerRegistry
from base.exploreBase import ExploreBaseHandler, ExploreResponse

from .utils import MOBILE_UA, parse_list_html


TAB_TYPES = [
    {"tab_type": 1, "title": "视频"},
    {"tab_type": 2, "title": "小说"},
    {"tab_type": 3, "title": "有声"},
    {"tab_type": 4, "title": "漫画"},
]


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


@HandlerRegistry.register
class UxxTabsHandler(ExploreBaseHandler):
    path = "/uxx/tabs"
    name = "uxx_tabs"
    methods = ["GET"]
    query_params = []
    description = "海阔视界分类标签列表"
    auth_required = False

    async def handle(self, **kwargs: Any) -> ExploreResponse:
        return ExploreResponse(bookList=TAB_TYPES)