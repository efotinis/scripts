"""Torrent file reader.

When run as a script, it pretty-prints the contents of the torrent files
specified as arguments (hash values excluded for brevity).

Exceptions thrown from this module:
- IOError: data read error
- AssertionError/ValueError: bad data

File format specs taken from:
    <http://wiki.theory.org/BitTorrentSpecification>
"""
import os
import re


intformat = re.compile(r'^(?:0|-?[1-9][0-9]*)$')


def readexactly(f, size):
    """Read an exact number of bytes."""
    ret = f.read(size)
    if len(ret) != size:
        raise IOError('unexpected end of data')
    return ret


def readto(f, delim):
    """Read up to a delimiter byte.

    The delimiter will be consumed, but it won't appear in the result.
    """
    ret = ''
    while True:
        c = readexactly(f, 1)
        if c == delim:
            return ret
        ret += c

    
"""
bencoding format
    ascii_num:  r'0|-?[1-9][0-9]*'
    item:       str | int | list | dict
    str:        ascii_num ':' ('ascii_num' bytes)
    int:        'i' ascii_num 'e'
    list:       'l' item+ 'e'
    dict:       'd' pair+ 'e'
    pair:       str item
"""


def readstr(f, lead=''):
    """Read a bencoded string. Accepts leading bytes that are already read."""
    size = int(lead + readto(f, ':'))
    assert size >= 0
    return readexactly(f, size)


def readint(f):
    """Read a bencoded integer (after leading 'i')."""
    s = readto(f, 'e')
    assert intformat.match(s)
    return int(s, 10)


def readlist(f):
    """Read a bencoded list (after leading 'l')."""
    ret = []
    while True:
        x = readvalue(f, checkend=True)
        if x is None:
            return ret
        ret += [x]
    

def readdict(f):
    """Read a bencoded dictionary (after leading 'd')."""
    ret = {}
    while True:
        c = readexactly(f, 1)
        if c == 'e':
            return ret
        key = readstr(f, c)
        ret[key] = readvalue(f)


def readvalue(f, checkend=False):
    """Read any bencoded value.

    Will return None if next char is 'e' and checkend=True.
    """
    c = readexactly(f, 1)
    if checkend and c == 'e':
        return None
    try:
        return {'i':readint, 'l':readlist, 'd':readdict}[c](f)
    except KeyError:
        return readstr(f, c)


if __name__ == '__main__':
    import sys
    import pprint
    args = sys.argv[1:]
    if not args:
        print 'no torrent files specified'
    else:
        for s in args:
            print s
            print '-' * 78
            data = readvalue(open(s, 'rb'))
            data['info']['pieces'] = '<hash data omitted>'
            pprint.pprint(data)
            print
