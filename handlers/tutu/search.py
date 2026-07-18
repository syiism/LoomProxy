from datetime import datetime, timedelta, timezone
from typing import Any

from ..base.searchBase import SearchBaseHandler, SearchResponse, BookItem
from ..base.base import HandlerRegistry

import re


def _strip_search_prefix(query: str) -> str:
    """去除 Legado 书源前缀 +1/+3/+11/+19 等（URL 中 + 可能被解码为空格）"""
    return re.sub(r"^[\s+]+\d+\s*", "", query)


GENDER_MAP = {"0": "女生", "1": "男生", "2": "出版"}
CREATION_STATUS_MAP = {"0": "完结", "1": "连载", "4": "断更", "-1": "未知"}
TZ_SHANGHAI = timezone(timedelta(hours=8))


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


def build_kind(item: dict[str, Any]) -> str:
    """拼接 kind：性别,评分,类型,状态,最近更新(YYYY-MM-dd)"""
    gender = GENDER_MAP.get(str(item.get("gender", "")), "未知")
    score = item.get("score", "") + '分'
    category = item.get("category", "")
    creation_status = CREATION_STATUS_MAP.get(str(item.get("creation_status", "")), "未知")

    last_update = ""
    ts = item.get("last_chapter_update_time", "")
    if ts:
        try:
            last_update = datetime.fromtimestamp(int(ts), tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return ",".join([gender, str(score), str(category), creation_status, last_update])


def build_video_kind(item: dict[str, Any]) -> str:
    """拼接视频项 kind：rec_text,sub_title(·替换为,)"""
    rec_text = item.get("rec_text", "")
    sub_title = item.get("sub_title", "").replace("·", ",")
    score = item.get("score", "") + '分'
    return ",".join([rec_text, score, sub_title])


def build_book_item(item: dict[str, Any], base_url: str) -> BookItem:
    """从 book_data 或 video_data 项构建 BookItem。"""
    if "book_name" in item:
        # 书籍项
        return BookItem(
            bookId=item.get("book_id", ""),
            name=item.get("book_name", ""),
            author=item.get("author", ""),
            kind=build_kind(item),
            wordCount=item.get("word_number", ""),
            lastChapter=item.get("last_chapter_title", ""),
            intro=item.get("abstract", ""),
            coverUrl=item.get("thumb_url", ""),
        )
    # 视频项
    return BookItem(
        bookId=item.get("series_id", ""),
        name=item.get("title", ""),
        author=item.get("copyright", ""),
        kind=build_video_kind(item),
        wordCount="",
        lastChapter="",
        intro=item.get("video_desc", ""),
        coverUrl=item.get("cover", "").strip(),
    )


@HandlerRegistry.register
class TutuSearchHandler(SearchBaseHandler):
    """tutu 搜索处理器"""
    path = "/tutu/search"
    name = "tutu_search"
    methods = ["GET"]
    query_params = ["base_url", "query", "offset", "count", "tab_type"]
    description = "tutu 搜索"

    async def handle(self, **kwargs: Any) -> SearchResponse:
        """处理搜索请求"""
        base_url = kwargs.get("base_url", "").rstrip('/')
        query = _strip_search_prefix(kwargs.get("query", ""))
        offset = kwargs.get("offset", "")
        count = kwargs.get("count", "")
        tab_type = kwargs.get("tab_type", "")

        api_base = base_url + "/api/v1" if not base_url.endswith("/api/v1") else base_url

        import httpx
        timeout = httpx.Timeout(10.0, connect=5.0)

        # 若 query 为纯数字 bookId，走详情接口封装为单条 bookList
        if query.isdigit() and len(query) > 5:
            url = f"{api_base}/books/{query}"
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url)
            resp.raise_for_status()
            detail_data = resp.json().get("data", {})
            item = build_book_item(detail_data, api_base)
            return SearchResponse(bookList=[item])

        url = f"{api_base}/search?query={query}&offset={offset}&count={count}&tab_type={tab_type}"

        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            data = await client.get(url)
        data.raise_for_status()
        data = data.json()

        search_tabs = data["search_tabs"]
        raw_list = parse_tab_item(search_tabs)
        book_list = [build_book_item(item, base_url) for item in raw_list]

        return SearchResponse(bookList=book_list)
