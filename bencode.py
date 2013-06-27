"""Bencode utilities.

Format specs:
    <http://wiki.theory.org/BitTorrentSpecification>
"""

import cStringIO
import fileutil
import re


def loads(s):
    """Read an object from a string."""
    return load(cStringIO.StringIO(s))


def load(f):
    """Read an object from a file."""
    return readany(f)


def dumps(obj):
    """Write an object to a string."""
    f = cStringIO.StringIO()
    dump(f, obj)
    return f.getvalue()


def dump(f, obj):
    """Write an object to a file."""
    writeany(f, obj)


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


INT_FORMAT = re.compile(r'^(?:0|-?[1-9][0-9]*)$')


def readstr(f, lead=''):
    """Read a bencoded string. Accepts leading bytes that are already read."""
    size = int(lead + fileutil.readupto(f, ':'))
    if size < 0:
        raise ValueError('bad string size')
    return fileutil.readexactly(f, size)


def readint(f):
    """Read a bencoded integer (after leading 'i')."""
    s = fileutil.readupto(f, 'e')
    if not INT_FORMAT.match(s):
        raise ValueError('bad integer')
    return int(s, 10)


def readlist(f):
    """Read a bencoded list (after leading 'l')."""
    ret = []
    while True:
        x = readany(f, checkend=True)
        if x is None:
            return ret
        ret += [x]
    

def readdict(f):
    """Read a bencoded dictionary (after leading 'd')."""
    ret = {}
    while True:
        c = fileutil.readexactly(f, 1)
        if c == 'e':
            return ret
        key = readstr(f, c)
        ret[key] = readany(f)


def readany(f, checkend=False):
    """Read any bencoded value.

    Will return None if next char is 'e' and checkend=True.
    """
    c = fileutil.readexactly(f, 1)
    if checkend and c == 'e':
        return None
    try:
        return {'i':readint, 'l':readlist, 'd':readdict}[c](f)
    except KeyError:
        return readstr(f, c)


def writeany(f, obj):
    """Write any bencoded value."""
    if isinstance(obj, dict):
        f.write('d')
        for k in sorted(obj):
            if not isinstance(k, str):
                raise TypeError('dict key is not a string')
            writeany(f, k)
            writeany(f, obj[k])
        f.write('e')
    elif isinstance(obj, list):
        f.write('l')
        for x in obj:
            writeany(f, x)
        f.write('e')
    elif isinstance(obj, str):
        f.write(str(len(obj)) + ':' + obj)
    else:
        f.write('i' + str(obj) + 'e')
