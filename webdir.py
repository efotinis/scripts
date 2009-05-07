"""Utilities for server directory listings."""

import urllib2
import BeautifulSoup
import re
import collections

# item information:
# - name [string]: dirs have trailing '/'
# - date [string]: usually in 'dd-MMM-yyyy hh:mm' format
# - size [int]: approximate
Item = collections.namedtuple('Item', 'name date size')

def stdreader(url):
    """Default page reader, returning a page's contents.
    Can be replaced with a custom (eg. caching) one."""
    return urllib2.urlopen(url).read()

def walk(top, reader=stdreader):
    _url, items = pagelist(top, reader)
    dirs, files = [], []
    for item in items:
        if item.name.endswith('/'):  # dir entry
            if item.name[:1] != '/':  # not the parent
                #dirs += [item._replace(name=item.name.rstrip('/'))]
                dirs += [item]
        else:
            files += [item]
    yield top, dirs, files
    for dir in dirs:
        for x,y,z in walk(top + dir.name, reader):
            yield x,y,z

_rxheader = re.compile(r'Index of (.*)')

def pagelist(url, reader=stdreader):
    html = reader(url)
    soup = BeautifulSoup.BeautifulSoup(html)
    body = soup.body
    curpath = _rxheader.match(body.h1.string).group(1)
    if body.pre:
        # Apache, eg: http://aldo061.free.fr/
        return curpath, _dirItemsFromPre(body.pre)
    elif body.table:
        # eg: http://galix.nexticom.net/~rebel/ircpics/
        rows = body.table.findAll('tr')
        return curpath, _dirItemsFromTableRows(rows)
    else:
        raise RuntimeError('unknown page format')

def _dirItemsFromTableRows(rows):
    for tr in rows:
        # skip header fields and header/footer <hr>s contained in <th>s
        if tr.th:
            continue
        cells = tr.findAll('td')[1:4]
        name = cells[0].a['href']
        date = cells[1].string.strip()
        size = cells[2].string.strip()
        if name.startswith('./'):
            # names containing special chars, like ':', have this
            name = name[2:]
        yield Item(name, date, str2size(size))

_rxpreitem = re.compile(r'''\s+
    (\d{2}-[a-z]{3}-\d{4}\ \d{2}:\d{2})  # date/time
    \s+
    ([\d+.]+[kmg]?|-)  # size
    .*\n''', re.IGNORECASE | re.VERBOSE)

def _dirItemsFromPre(pre):
    children = pre.childGenerator()
    for item in children:
        if not item.string and item.name == 'hr':
            children.next()  # skip '\n'
            break
    while True:
        try:
            children.next()  # <img>
            children.next()  # ' '
            a = children.next()  # <a>
            info = children.next()  # '   dd-MMM-yyyy hh:mm   size  descr\n'
            name = a['href']
            date, size = _rxpreitem.match(info).groups()
            yield Item(name, date, str2size(size))
        except StopIteration:
            break

_rxsize = re.compile(r'(-)|([0-9.]+)([kmg]?)', re.IGNORECASE)
_unitmult = {'':1, 'k':2**10, 'm':2**20, 'g':2**30}

def str2size(s):
    """Convert size string to bytes. Accepts a single dash and trailing units."""
    dash, num, unit = _rxsize.match(s).groups()
    return 0 if dash else int(float(num) * _unitmult[unit.lower()])
