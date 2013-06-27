import os
import sys
import BeautifulSoup as bs
import urllib2
import pickle
from CommonTools import conout


def readAsBrowser(url):
    """Read an URL using a popular user-agent string.
    Needed for sites like Wikipedia that block unknown agents."""
    request = urllib2.Request(url, headers={'User-Agent':'Opera'})
    return urllib2.urlopen(request).read()


def tableRows(soup):
    """Generate the rows of the single table in the page
    as 3-tuples of non-text elements (TH or TD)."""
    tables = soup.findAll('table', 'wikitable')
    assert len(tables) == 1, 'more than 1 tables found'
    for row in tables[0].findAll('tr'):
        elems = [x for x in row.contents if not isinstance(x, bs.NavigableString)]
        assert len(elems) == 3, 'table row does not have exactly 3 elements'
        yield elems


def contentsString(elem):
    """Convert an element to plain text."""
    return ''.join(
        child.string or contentsString(child)
        for child in elem.contents)


def countryCodes(soup):
    """Generate the (ID,name,info) of the ccTLDs."""
    curType = ''
    for id, name, info in tableRows(soup):
        if id.name == 'th':
            curType = contentsString(id)
        elif curType == 'ccTLD':
            yield map(lambda x: contentsString(x).strip(), (id, name, info))
            

def loadData():
    """Load (or generate & save) a dict of 2-letter codes to country/info pairs."""
    DATAFILE = os.path.splitext(sys.argv[0])[0] + '.dat'
    try:
        data = pickle.load(open(DATAFILE, 'rb'))
    except IOError:
        html = readAsBrowser('http://en.wikipedia.org/wiki/List_of_Internet_top-level_domains')
        soup = bs.BeautifulSoup(html, convertEntities=bs.BeautifulSoup.HTML_ENTITIES)
        data = dict((id.lstrip('.'), (name, info))
                    for id, name, info in countryCodes(soup))
        try:
            pickle.dump(data, open(DATAFILE, 'wb'), pickle.HIGHEST_PROTOCOL)
        except IOError:
            pass
    return data


def showhelp():
    print '''
Display country name (and some info if available) of 2-letter TLDs.

CCTLD [tld ...]

  tld  A 2-letter TLD. Leading dots are ignored.
'''[1:-1]


def main(args):
    if '/?' in args:
        showhelp()
        return 0
    if not args:
        return 0
    d = loadData()
    args = [s.lower().lstrip('.') for s in args]
    allok = True
    for s in args:
        print s + ':',
        try:
            country, note = d[s]
            print country
            if note:
                conout('   ', note)
        except KeyError:
            print 'UNUSED'
            allok = False
    return 0 if allok else 1
            

sys.exit(main(sys.argv[1:]))
