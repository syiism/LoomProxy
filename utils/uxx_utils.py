import re

from lxml import html as lxml_html

from base.searchBase import BookItem


MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36"


def extract_book_id(href: str) -> str:
    match = re.search(r'/(?:play|show)/([^/]+?)(?:/|\.html|$)', href)
    return match.group(1) if match else ''


def parse_list_html(html_text: str) -> list[BookItem]:
    tree = lxml_html.fromstring(html_text)
    book_list = []

    items = tree.xpath('//*[contains(@class, "list_1_box") or contains(@class, "list_3_box")]//li')
    for item in items:
        a_elements = item.xpath('.//a')
        if not a_elements:
            continue
        a_tag = a_elements[0]

        title = (a_tag.get('title') or '').strip()
        href = a_tag.get('href') or ''

        img_elements = item.xpath('.//div[contains(@class, "cover_box")]//img')
        img = img_elements[0].get('src') if img_elements else ''

        # state（连载中/已完结等）
        state_elements = item.xpath('.//div[contains(@class, "state")]/text()')
        state = state_elements[0].strip() if state_elements else ''

        # 两个 info_box：第一个含 author + 分类，第二个含时间 + 浏览量
        info_boxes = item.xpath('.//div[contains(@class, "info_box")]')

        author = ''
        category = ''
        update_time = ''
        views = ''

        if len(info_boxes) >= 1:
            author_elements = info_boxes[0].xpath('.//div[contains(@class, "author")]/text()')
            author = author_elements[0].strip() if author_elements else ''

            category_elements = info_boxes[0].xpath('.//div[contains(@class, "view")]//span/text()')
            category = category_elements[0].strip() if category_elements else ''

        if len(info_boxes) >= 2:
            time_elements = info_boxes[1].xpath('.//div[contains(@class, "author")]/text()')
            update_time = time_elements[0].strip() if time_elements else ''

            view_elements = info_boxes[1].xpath('.//div[contains(@class, "view")]//span/text()')
            views = view_elements[0].strip() if view_elements else ''

        # kind: state, category, update_time, views 拼接
        kind_parts = [p for p in [state, category, update_time, '👁'+views] if p]
        kind = ','.join(kind_parts)

        book_id = extract_book_id(href)

        book_list.append(BookItem(
            bookId=book_id,
            name=title,
            author=author,
            kind=kind,
            wordCount='',
            lastChapter='',
            intro='',
            coverUrl=img,
        ))

    return book_list