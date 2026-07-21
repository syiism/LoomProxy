from typing import Any

from bs4 import BeautifulSoup

from base.base import HandlerRegistry
from base.searchBase import SearchBaseHandler, SearchResponse, BookItem


MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"


def extract_book_id(href: str) -> str:
    parts = href.strip('/').split('/')
    if len(parts) >= 2 and parts[0] == 'play':
        return parts[1]
    return ''


def parse_search_html(html: str) -> list[BookItem]:
    soup = BeautifulSoup(html, "html.parser")
    book_list = []
    
    items = soup.select('.list_1_box li')
    for item in items:
        a_tag = item.find('a')
        if not a_tag:
            continue
        
        title = a_tag.get('title', '').strip()
        href = a_tag.get('href', '')
        
        img_tag = item.find('img')
        img = img_tag.get('src', '') if img_tag else ''
        
        info_box = item.select_one('.info_box')
        desc = info_box.get_text(strip=True) if info_box else ''
        
        book_id = extract_book_id(href)
        
        book_list.append(BookItem(
            bookId=book_id,
            name=title,
            author='',
            kind='',
            wordCount='',
            lastChapter='',
            intro='',
            coverUrl=img,
        ))
    
    return book_list


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
        
        book_list = parse_search_html(html)
        
        return SearchResponse(bookList=book_list)