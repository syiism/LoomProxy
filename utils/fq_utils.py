from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from base.searchBase import BookItem

TZ_SHANGHAI = timezone(timedelta(hours=8))

GENDER_MAP = {"0": "女生", "1": "男生", "2": "出版"}
CREATION_STATUS_MAP = {"0": "完结", "1": "连载", "4": "断更", "-1": "未知"}

_STRIP_PREFIX_RE = re.compile(r"^[\s+]+\d+\s*")


def normalize_api_base(base_url: str, prefix: str = "/api") -> str:
    base = base_url.rstrip("/")
    if base.endswith(prefix):
        return base
    return base + prefix


def strip_search_prefix(query: str) -> str:
    return _STRIP_PREFIX_RE.sub("", query)


def normalize_video_item(item: dict[str, Any]) -> None:
    card_tips = item.get("card_tips", "")
    if not item.get("rec_text") and card_tips:
        parts = card_tips.split("·")
        item["rec_text"] = parts[-1] if len(parts) > 1 else card_tips
    if not item.get("sub_title"):
        if card_tips:
            parts = card_tips.split("·")
            if len(parts) >= 3:
                item["sub_title"] = "·".join(parts[:-1])
            elif len(parts) == 2:
                item["sub_title"] = parts[0]
        else:
            sil = item.get("secondary_info_list", [])
            if sil:
                item["sub_title"] = "·".join(s.get("content", "") for s in sil)
            else:
                stl = item.get("sub_title_list", [])
                if stl:
                    item["sub_title"] = "·".join(s.get("content", "") for s in stl)


def extract_book_data(obj: Any, depth: int = 0, max_depth: int = 9) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if depth > max_depth:
        return items
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "book_data" and isinstance(v, list):
                items.extend(item for item in v if isinstance(item, dict) and item.get("book_id"))
            elif k == "video_data" and isinstance(v, list):
                items.extend(item for item in v if isinstance(item, dict) and item.get("series_id"))
            else:
                items.extend(extract_book_data(v, depth + 1, max_depth))
    elif isinstance(obj, list):
        for item in obj:
            items.extend(extract_book_data(item, depth + 1, max_depth))
    return items


def build_book_kind(item: dict[str, Any]) -> str:
    gender = GENDER_MAP.get(str(item.get("gender", "")), "未知")
    score = item.get("score", "") + "分"
    category = item.get("category", "")
    creation_status = CREATION_STATUS_MAP.get(str(item.get("creation_status", "")), "未知")
    ts = item.get("last_publish_time") or item.get("last_chapter_update_time", "")
    last_update = ""
    if ts:
        try:
            last_update = datetime.fromtimestamp(int(ts), tz=TZ_SHANGHAI).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
    return ",".join([gender, str(score), str(category), creation_status, last_update])


def build_video_kind(item: dict[str, Any]) -> str:
    normalize_video_item(item)
    rec_text = item.get("rec_text", "")
    score = item.get("score", "") + "分"
    sub_title = item.get("sub_title", "").replace("·", ",")
    return ",".join([rec_text, score, sub_title])


def build_book_item(item: dict[str, Any]) -> BookItem:
    if "book_name" in item:
        return BookItem(
            bookId=item.get("book_id", ""),
            name=item.get("book_name", ""),
            author=item.get("author", ""),
            kind=build_book_kind(item),
            wordCount=str(item.get("word_number", "")),
            lastChapter=item.get("last_chapter_title", ""),
            intro=item.get("abstract", ""),
            coverUrl=item.get("thumb_url", ""),
        )
    return BookItem(
        bookId=item.get("series_id", ""),
        name=item.get("title", ""),
        author=item.get("copyright", ""),
        kind=build_video_kind(item),
        wordCount="",
        lastChapter="",
        intro=item.get("video_detail", {}).get("series_intro", "") or item.get("video_desc", ""),
        coverUrl=item.get("cover", "").strip(),
    )


_BOOK_TYPE_CODE_MAP = {
    "xiaoshuo": 8,
    "tingshu": 32,
    "duanju": 4,
    "manju": 4,
    "manhua": 64,
}


def _detect_book_type(data: dict[str, Any]) -> str:
    book_type = data.get("book_type", "")
    genre = data.get("genre", "")
    is_ebook = data.get("is_ebook", "")
    comic_book_type = data.get("comic_book_type")
    playlet_book_id = data.get("playlet_book_id")
    schedule_mode = data.get("schedule_mode")
    album_book_order = data.get("album_book_order")

    if book_type == "1" or genre == "4":
        return "tingshu"
    if comic_book_type is not None or genre == "1":
        return "manhua"
    if playlet_book_id is not None:
        return "duanju"
    if genre == "205" and schedule_mode is not None:
        if album_book_order is not None:
            return "duanju"
        return "manju"
    if genre == "203":
        return "duanju"
    if is_ebook == "1" or genre == "0":
        return "xiaoshuo"
    return "xiaoshuo"


def book_type_code(book_type: str) -> int:
    return _BOOK_TYPE_CODE_MAP.get(book_type, 8)
