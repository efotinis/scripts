import sys
import argparse
import urllib2
import BeautifulSoup
import webutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='list image URLs from a 4chan thread',
        add_help=False)
    add = ap.add_argument
    add('page_url', metavar='URL', help='page URL')
    add('-?', action='help', help='this help')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    try:
        html = webutil.wget(args.page_url)
    except urllib2.HTTPError as err:
        if err.code == 404:
            sys.exit(str(err))
        else:
            raise
    sp = BeautifulSoup.BeautifulSoup(html, convertEntities='html')

    for a in sp.findAll('a', 'fileThumb'):
        url = a['href']
        if 'images.4chan.org' in url:
            print 'http:' + url
