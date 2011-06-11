"""Get the next sunrise or sunset time of a place using Google.

Searching on Google for "sunrise <town> <country>" will display the time
of the next sunrise (same for sunset) above the search results.
"""

import re
import urllib
import urllib2
import BeautifulSoup
import argparse


def parse_args():
    ap = argparse.ArgumentParser(add_help=False,
        description='get the next sunrise or sunset time')
    ap.add_argument('-s', dest='sunset', action='store_true',
                    help='get sunset time; default is sunrise')
    ap.add_argument('place', metavar='PLACE',
                    help='name of town, city or place')
    ap.add_argument('country', metavar='COUNTRY', nargs='?',
                    help='country name; use this if the place name alone doesn\'t work')
    ap.add_argument('-?', action='help', help='this help')
    return ap.parse_args()


def to_str(elem):
    """Convert a BeautifulSoup element to plain text."""
    if elem.string is not None:
        return re.sub(r'\s+', ' ', elem.string)
    elif elem.name == 'br':
        return '\n'
    else:
        return ''.join(to_str(sub) for sub in elem.contents)


if __name__ == '__main__':
    args = parse_args()

    query = 'sunset' if args.sunset else 'sunrise'
    query += ' ' + args.place
    if args.country:
        query += ' ' + args.country

    url = 'http://www.google.com/search?' + urllib.urlencode({'q':query})
    req = urllib2.Request(url, headers={'User-Agent':'Opera'})
    html = urllib2.urlopen(req).read()
    soup = BeautifulSoup.BeautifulSoup(html)

    ob = soup.find('table', 'obcontainer')
    if not ob:
        raise SystemExit('could not find response')

    print to_str(ob.table.tr.td.nextSibling).strip()
