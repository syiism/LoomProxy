from typing import Any

from bs4 import BeautifulSoup

from base.base import HandlerRegistry
from base.detailBase import DetailBaseHandler, BookDetail


MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"


def detect_book_type(html: str, soup: BeautifulSoup) -> tuple[str, int]:
    title = soup.title.get_text(strip=True) if soup.title else ''
    brief = soup.select_one('.brief')
    intro = brief.get_text(strip=True) if brief else ''
    
    if '小说' in title or '小说简介' in intro or '小说' in intro:
        return 'novel', 8
    
    if '漫画' in title or '.webp' in html:
        return 'manga', 64
    
    return 'video', 4


def parse_detail_html(html: str, book_id: str) -> BookDetail:
    soup = BeautifulSoup(html, "html.parser")
    
    title = soup.h1.get_text(strip=True) if soup.h1 else ''
    
    info_items = soup.select('.info_box .item')
    author = ''
    status = ''
    last_chapter = ''
    last_update = ''
    
    if len(info_items) >= 1:
        last_chapter = info_items[0].get_text(strip=True)
    if len(info_items) >= 2:
        last_update = info_items[1].get_text(strip=True)
    if len(info_items) >= 3:
        author = info_items[2].get_text(strip=True).replace('/', ' ')
    
    update_state = soup.select_one('.update_state')
    status = update_state.get_text(strip=True) if update_state else ''
    
    cover_img = soup.select_one('.main_box .content_box img')
    cover_url = cover_img.get('src', '') if cover_img else ''
    
    brief = soup.select_one('.brief')
    intro = brief.get_text(strip=True).replace('收起', '') if brief else ''
    
    book_type, book_type_code = detect_book_type(html, soup)
    
    return BookDetail(
        bookType=book_type,
        bookTypeCode=book_type_code,
        authorId='',
        bookId=book_id,
        name=title,
        aliasName='',
        author=author,
        status=status,
        createTime='',
        lastUpdateTime=last_update,
        wordCount='',
        category='',
        tags='',
        roles='',
        tones='',
        score='',
        readCount='',
        source='海阔视界',
        intro=intro,
        copyright='',
        bookReview='无',
        coverUrl=cover_url,
        lastChapter=last_chapter,
    )


@HandlerRegistry.register
class UxxDetailHandler(DetailBaseHandler):
    path = "/uxx/detail"
    name = "uxx_detail"
    methods = ["GET"]
    query_params = ["book_id"]
    description = "海阔视界详情"
    auth_required = False

    async def handle(self, **kwargs: Any) -> BookDetail:
        book_id = kwargs.get("book_id", "").strip()
        
        url = f"https://www.uxx001.com/show/{book_id}.html"
        
        resp = await self.fetch(url, headers={"User-Agent": MOBILE_UA})
        resp.raise_for_status()
        html = resp.text
        
        return parse_detail_html(html, book_id)