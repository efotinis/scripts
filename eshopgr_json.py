""""Scrape product listings from e-shop.gr in JSON format."""

import argparse
import collections
import itertools
import json
import logging
import re
import time
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup


QS_ENC = 'ISO-8859-7'  # query string encoding (may be Windows-1253)
NO_ZERO_OFFSET = True  # omit 0 offset in queries, like site does (optional)


# TODO: change fields to full names
Item = collections.namedtuple('Item', 'title url pid price discount cat sub man')


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
        '-v',
        dest='verbose',
        action='store_true',
        help='verbose output'
    )
    args = ap.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    return args


##def listing(url):
##    parts = urlsplit(url)
##    query = parse_qs(parts.query, encoding=QS_ENC)
##    for offset in itertools.count(0, 10):
##        if offset != 0:
##            query['offset'] = offset
##        elif 'offset' in query and NO_ZERO_OFFSET:
##            del query['offset']
##        yield urlunsplit(parts._replace(query=urlencode(
##            query, doseq=True, encoding=QS_ENC)))


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
            # find 'EKPTOSI ...'
            m = re.match(r'\u0395\u039a\u03a0\u03a4\u03a9\u03a3\u0397\s+(.+)', font_elems[1].text)
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

        #yield Item(title=title, url=url, pid=pid, price=price, discount=discount)
        yield Item(**data)
        item_index += 1


def page_next(soup):
    a = soup.find('a', 'mobile_list_navigation_link', text='>')
    return a['href'] if a else ''


def listing(url, delay=0.2):
    page_index = 1
    while url:
        time.sleep(delay)
        logging.info(f'processing page {page_index}')
        soup = BeautifulSoup(requests.get(url).text, 'lxml')
        yield from page_items(soup)
        url = page_next(soup)
        page_index += 1


def main(args):
    for u in args.url:
        for item in listing(u):
            # - replace Decimal price with string, since JSON can't handle it
            # - convert to plain dict, since _asdict() returns OrderedDict
            print(json.dumps(dict(item._replace(price=str(item.price))._asdict())))


if __name__ == '__main__':
    main(parse_args())


##
####    #URL = 'https://www.e-shop.gr/eidi-grafeiou-mpataries-list?table=ANA&category=%CC%D0%C1%D4%C1%D1%C9%C5%D3'
####    # external hdds; Seagate
####    URL = 'https://www.e-shop.gr/ypologistes-eksoterikoi-skliroi-diskoi-seagate-list?table=PER&category=%C5%CE%D9%D4%C5%D1%C9%CA%CF%C9+%C4%C9%D3%CA%CF%C9&filter-7145=1'
##    # CPUs
##    URL = 'https://www.e-shop.gr/ypologistes-epeksergastes-cpu-list?table=PER&category=%C5%D0%C5%CE%C5%D1%C3%C1%D3%D4%C7%D3+-+CPU'
##    a = list(listing(URL))
