# encoding: utf-8
""""Scrape product listings from e-shop.gr in JSON format."""

import argparse
import collections
import json
import logging
import re
import time

import requests

from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode
from bs4 import BeautifulSoup


# TODO: change fields to full names
Item = collections.namedtuple(
    'Item',
    'title url pid price discount cat sub man'
)


def parse_args():
    ap = argparse.ArgumentParser(
        description='Generate JSON info of e-shop.gr product listings.'
    )
    ap.add_argument(
        'url',
        nargs='+',
        help='list URL'
    )
    ap.add_argument(
        '-d',
        dest='delay',
        type=float,
        default=0.2,
        help='delay between network calls in seconds; default: %(default)s'
    )
    ap.add_argument(
        '-v',
        dest='verbose',
        action='store_true',
        help='verbose output'
    )
    args = ap.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    return args


def page_items(soup):
    item_index = 1
    for cont in soup.find_all('table', 'web-product-container'):
        logging.info(f'processing item {item_index}')
        data = {}
        data['title'] = cont.find('h2').text
        data['url'] = cont.find('a', 'web-title-link')['href']

        font_elems = cont.find_all('font', limit=2)
        data['pid'] = font_elems[0].text.strip('()')
        data['discount'] = ''
        if len(font_elems) > 1:
            m = re.match(r'ΕΚΠΤΩΣΗ\s+(.+)', font_elems[1].text)
            if m:
                data['discount'] = m.group(1)

        td = cont.find('td', 'web-product-price')
        font = td.font
        data['price'] = Decimal(font.text if font else td.b.text)

        td = cont.find('td', 'web-product-info')
        fields = {
            'Κατηγορία:': 'cat',
            'Υποκατηγορία:': 'sub',
            'Κατασκευαστής:': 'man'
        }
        data.update(dict.fromkeys(fields.values(), ''))
        for b in td.find_all('b', recursive=False, limit=3):
            data[fields[b.text]] = b.next_sibling.strip()

        yield Item(**data)
        item_index += 1


def get_next_page_url_or_none(soup):
    a = soup.find('a', 'mobile_list_navigation_link', text='>')
    return a['href'] if a else None


def get_products(url, delay):
    page_index = 1
    while url:
        time.sleep(delay)
        logging.info(f'processing page {page_index}')
        soup = BeautifulSoup(requests.get(url).text, 'lxml')
        yield from page_items(soup)
        url = get_next_page_url_or_none(soup)
        page_index += 1


def main(args):
    for u in args.url:
        for item in get_products(u, args.delay):
            item = item._replace(price=str(item.price))  # replace Decimal
            print(json.dumps(item._asdict()))


if __name__ == '__main__':
    main(parse_args())
