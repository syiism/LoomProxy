from typing import Any

import re
from bs4 import BeautifulSoup

from base.base import HandlerRegistry
from base.contentBase import ContentBaseHandler, ContentResponse


MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"


async def fetch_video_content(fetch, url: str) -> ContentResponse:
    resp = await fetch(url, headers={"User-Agent": MOBILE_UA})
    resp.raise_for_status()
    html = resp.text
    
    if "video_box" in html:
        soup = BeautifulSoup(html, "html.parser")
        player = soup.select_one('#mui-player')
        if player:
            src = player.get('src', '')
            if src:
                return ContentResponse(contentType="video", data={"content": src})
    
    return ContentResponse(contentType="error", data={"message": "无法找到视频源"})


async def fetch_audio_content(fetch, url: str) -> ContentResponse:
    resp = await fetch(url, headers={"User-Agent": MOBILE_UA})
    resp.raise_for_status()
    html = resp.text
    
    if "mp3" in html:
        soup = BeautifulSoup(html, "html.parser")
        player = soup.select_one('#player')
        if player:
            src = player.get('src', '')
            if src:
                return ContentResponse(contentType="audio", data={"content": src, "isMusic": True})
    
    return ContentResponse(contentType="error", data={"message": "无法找到音频源"})


async def fetch_novel_content(fetch, url: str) -> ContentResponse:
    headers = {
        "User-Agent": MOBILE_UA
    }
    
    resp = await fetch(url, headers=headers)
    resp.raise_for_status()
    html = resp.text
    
    soup = BeautifulSoup(html, "html.parser")
    
    chapter_title = soup.select_one('.style_h1')
    title = chapter_title.get_text(strip=True).replace('（', '').replace('）', '') if chapter_title else ''
    
    pattern = r'\$\.get\s*\(\s*["\']([^"\']+)["\']'
    match = re.search(pattern, html)
    if not match:
        pattern2 = r'_getcontent\.php[^"\'\s]+'
        match2 = re.search(pattern2, html)
        if match2:
            content_path = match2.group(0)
            if not content_path.startswith('/'):
                content_path = '/' + content_path
        else:
            return ContentResponse(contentType="error", data={"message": "无法找到内容URL"})
    else:
        content_path = match.group(1)
    
    content_url = f"https://www.uxx001.com{content_path}"
    
    content_headers = {
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": MOBILE_UA,
        "Referer": url
    }
    
    content_resp = await fetch(content_url, headers=content_headers)
    content_resp.raise_for_status()
    content_text = content_resp.text
    
    if content_text == "readerror":
        return ContentResponse(contentType="error", data={"message": "读取错误"})
    
    content = f"<b><big>{title}</big></b><br><p>{content_text}</p>"
    return ContentResponse(contentType="novel", data={"content": content})


@HandlerRegistry.register
class UxxContentHandler(ContentBaseHandler):
    path = "/uxx/content"
    name = "uxx_content"
    methods = ["GET"]
    query_params = ["book_id", "item_id"]
    description = "海阔视界内容（自动识别视频/音频/小说）"
    auth_required = False

    async def handle(self, **kwargs: Any) -> ContentResponse:
        book_id = kwargs.get("book_id", "").strip()
        item_id = kwargs.get("item_id", "").strip()
        
        url = f"https://www.uxx001.com/play/{book_id}/0/{item_id}.html"
        
        resp = await self.fetch(url, headers={"User-Agent": MOBILE_UA})
        resp.raise_for_status()
        html = resp.text
        
        if "video_box" in html:
            return await fetch_video_content(self.fetch, url)
        elif "mp3" in html:
            return await fetch_audio_content(self.fetch, url)
        else:
            return await fetch_novel_content(self.fetch, url)