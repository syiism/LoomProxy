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

        img_elements = item.xpath('.//img')
        img = img_elements[0].get('src') if img_elements else ''

        info_elements = item.xpath('.//*[contains(@class, "info_box")]')
        desc = ''.join(info_elements[0].itertext()).strip() if info_elements else ''

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