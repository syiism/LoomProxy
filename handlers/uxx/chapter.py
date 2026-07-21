from typing import Any

from bs4 import BeautifulSoup

from base.base import HandlerRegistry
from base.chapterBase import ChapterBaseHandler, ChapterResponse, ChapterItem


MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"


def extract_item_id(href: str) -> str:
    parts = href.strip('/').split('/')
    if len(parts) >= 4:
        return parts[-1].replace('.html', '')
    return ''


def parse_chapters_html(html: str) -> list[ChapterItem]:
    soup = BeautifulSoup(html, "html.parser")
    
    chapters = []
    
    catalog_uls = soup.select('.catalog_ul')
    for ul in catalog_uls:
        links = ul.select('a')
        for link in links:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not href:
                continue
            
            item_id = extract_item_id(href)
            
            chapters.append(ChapterItem(
                title=title,
                itemId=item_id,
                chapterInfo='',
            ))
    
    return chapters


@HandlerRegistry.register
class UxxChapterHandler(ChapterBaseHandler):
    path = "/uxx/chapter"
    name = "uxx_chapter"
    methods = ["GET"]
    query_params = ["book_id"]
    description = "海阔视界章节"
    auth_required = False

    async def handle(self, **kwargs: Any) -> ChapterResponse:
        book_id = kwargs.get("book_id", "").strip()
        
        url = f"https://www.uxx001.com/show/{book_id}.html"
        
        resp = await self.fetch(url, headers={"User-Agent": MOBILE_UA})
        resp.raise_for_status()
        html = resp.text
        
        chapters = parse_chapters_html(html)
        
        return ChapterResponse(chapterList=chapters, nextTocUrl=None)