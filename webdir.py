"""Utilities for server directory listings."""

import urllib2
import BeautifulSoup
import re
import collections
import sys

# item information:
# - name [string]: dirs have trailing '/'
# - date [string]: usually in 'dd-MMM-yyyy hh:mm' format
# - size [int]: approximate
Item = collections.namedtuple('Item', 'name date size')

class PageError(Exception):
    def __init__(self, httperror):
        """httperror may be (str,url,code,msg) instead of an
        HTTPError object (to bypass the unpickling of Exceptions
        problem)"""
        if isinstance(httperror, urllib2.HTTPError):
            Exception.__init__(self, str(httperror))
            self.url = httperror.url
            self.code = httperror.code
            self.msg = httperror.msg
        else:
            Exception.__init__(self, httperror[0])
            self.url, self.code, self.msg = httperror[1:]

class UnknownListingFormat(Exception):
    pass

def stdreader(url):
    """Default page reader, returning a page's contents.
    Can be replaced with a custom (eg. caching) one."""
    try:
        return urllib2.urlopen(url).read()
    except HTTPError as err:
        raise PageError(err)

def stdhandler(err):
    """Default error handler, printing exception to stderr."""
    print >>sys.stderr, err

def walk(top, reader=stdreader, handler=stdhandler):
    try:
        html = reader(top)
        print '*' * 10, top
        _url, items = pagelist(html)
    except (PageError, UnknownListingFormat) as err:
        handler(err)
        return
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
        for x,y,z in walk(top + dir.name, reader, handler):
            yield x,y,z

_rxheader = re.compile(r'Index of (.*)')

def pagelist(html):
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
        raise UnknownListingFormat

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
    (\d{2}-[a-z]{3}-\d{4}\ \d{2}:\d{2})?  # date/time; optional
    \s+
    ([\d+.]+[kmg]?|-)  # size
    .*\n''', re.IGNORECASE | re.VERBOSE)

def _dirItemsFromPre(pre):
    # the '\n' after the <hr> isn't always present
##    children = pre.childGenerator()
##    for item in children:
##        if not item.string and item.name == 'hr':
##            children.next()  # skip '\n'
##            break
##    while True:
##        try:
##            children.next()  # <img>
##            children.next()  # ' '
##            a = children.next()  # <a>
##            info = children.next()  # '   dd-MMM-yyyy hh:mm   size  descr\n'
##            name = a['href']
##            date, size = _rxpreitem.match(info).groups()
##            yield Item(name, date, str2size(size))
##        except StopIteration:
##            break

    # the entries start with <img> and are between 2 <hr>
    items = pre.findAll(set(('img','hr')))
    hr_indices = [i for i,x in enumerate(items) if x.name == 'hr']
    assert len(hr_indices) == 2, '<pre> listing must have exactly 2 <hr>s'
    i, j = hr_indices
    for img in items[i+1:j]:
        a = img.next.next  # skip ' '
        info = a.nextSibling  # '   dd-MMM-yyyy hh:mm   size  descr\n'
        name = a['href']
        date, size = _rxpreitem.match(info).groups()
        yield Item(name, date, str2size(size))

_rxsize = re.compile(r'(-)|([0-9.]+)([kmg]?)', re.IGNORECASE)
_unitmult = {'':1, 'k':2**10, 'm':2**20, 'g':2**30}

def str2size(s):
    """Convert size string to bytes. Accepts a single dash and trailing units."""
    dash, num, unit = _rxsize.match(s).groups()
    return 0 if dash else int(float(num) * _unitmult[unit.lower()])

if __name__ == '__main__':
    #html = urllib2.urlopen('http://nfig.hd.free.fr/util/').read()
    path, items = pagelist(html)
    print path
    for item in items:
        print item
