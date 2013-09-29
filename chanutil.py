"""Get image boards resource URLs.

tags: web
compat: 2.7+, 3.3+
platform: any
"""

from __future__ import print_function
import re
import sys
import argparse
try:
    import urllib2
    import urlparse
    urllib_split = urlparse.urlsplit
    urllib_HTTPError = urllib2.HTTPError
except ImportError:
    import urllib.parse
    import urllib.error
    urllib_split = urllib.parse.urlsplit
    urllib_HTTPError = urllib.error.HTTPError

from bs4 import BeautifulSoup

import webutil


class Error(Exception): pass
class UrlError(Error): pass


# ---- site-specific functions ---- {{


def gen_images_4chan(bsoup):
    for a in bsoup.find_all('a', 'fileThumb'):
        url = a['href']
        if 'images.4chan.org' in url:
            yield 'http:' + url


# }} ---- site-specific functions ----


# map domains to (name, path-regex, image-function)
SITES = {
    'boards.4chan.org': ('4chan', re.compile(r'/([a-z]+)/res/(\d+)'), gen_images_4chan),
}


def get_page_info(url):
    """Get the site/board/thread/imgfunc from the target URL, if supported."""
    x = urllib_split(url.lower())
    try:
        name, rx, img_gen = SITES[x.netloc]
    except KeyError:
        raise UrlError('unsupported site: ' + x.netloc)
    try:
        board, thread = rx.match(x.path).groups()
    except AttributeError:
        raise UrlError('unexpected URL: ' + x.path)
    return (name, board, thread, img_gen)
    

def parse_args():
    ap = argparse.ArgumentParser(
        description='list resource URLs from an imageboard thread',
        add_help=False)
    add = ap.add_argument
    add('url', help='thread URL')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    try:
        _, _, _, img_gen = get_page_info(args.url)
    except UrlError as x:
        sys.exit(x)

    try:
        html = webutil.wget(args.url)
    except urllib_HTTPError as err:
        if err.code == 404:
            sys.exit('page not found')
        raise

    bsoup = BeautifulSoup(html)
    for s in img_gen(bsoup):
        print(s)
