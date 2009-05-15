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

class Error(Exception):
    """Base module error."""
    pass

class LoadError(Error):
    """HTTP error (4xx/5xx)."""
    pass    

class FormatError(Error):
    """Unrecognized listing format."""
    pass    

def stdreader(url):
    """Default page reader, returning a page's contents.
    Can be replaced with a custom (eg. caching) one."""
    try:
        return urllib2.urlopen(url).read()
    except urllib2.HTTPError as err:
        raise LoadError(str(err))

def stdhandler(err, url):
    """Default error handler prints to stderr."""
    print >>sys.stderr, err, url

def walk(top, reader=stdreader, handler=stdhandler):
    try:
        html = reader(top)
        _url, items = pagelist(html)
    except Error as err:
        handler(err, top)
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
    try:
        if body.h1.string == 'Index of locally available sites:':
            # HTTrack index page
            # e.g. http://nfig.hd.free.fr/util/WSML/wsmo/
            raise AttributeError
        curpath = _rxheader.match(body.h1.string).group(1)
    except (AttributeError, TypeError):
        # TypeError is raised when contents of <h1> are not a simpe string
        # e.g. http://nfig.hd.free.fr/util/material/ontology/OWL restrictions_fichiers/
        raise FormatError('no <h1> found')
    if body.pre:
        # Apache, eg: http://aldo061.free.fr/
        return curpath, _dirItemsFromPre(body.pre)
    elif body.table:
        # eg: http://galix.nexticom.net/~rebel/ircpics/
        rows = body.table.findAll('tr')
        return curpath, _dirItemsFromTableRows(rows)
    else:
        raise FormatError('unknown listing format')

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
    # the entries start with <img> and are between 2 <hr>
    items = pre.findAll(set(('img','hr')))
    hr_indices = [i for i,x in enumerate(items) if x.name == 'hr']
    # sometimes the second <hr> is right after the </pre>
    # eg: http://david.gharib.free.fr/
    assert 1 <= len(hr_indices) <= 2, '<pre> listing must have exactly 1 or 2 <hr>s'
    if (len(hr_indices) == 1):
        hr_indices += [None]  # will slice list to the end
    i, j = hr_indices
    for img in items[i+1:j]:
        a = img.next.next  # skip ' '
        # descr is usually truncuated so it's pretty useless
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
