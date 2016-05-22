"""Bencode utilities.

Format specs:
    <http://wiki.theory.org/BitTorrentSpecification>
"""

import re
try:
    from cStringIO import StringIO as DataIO
    str2bytes = lambda s: s
except ImportError:
    from io import BytesIO as DataIO
    str2bytes = lambda s: s.encode('latin1')

import fileutil


def loads(s):
    """Read an object from a string."""
    return load(DataIO(s))


def load(f):
    """Read an object from a file (or file path)."""
    if not hasattr(f, 'read'):
        f = open(f, 'rb')
    return readany(f)


def dumps(obj):
    """Write an object to a string."""
    f = DataIO()
    dump(f, obj)
    return f.getvalue()


def dump(f, obj):
    """Write an object to a file (or file path)."""
    if not hasattr(f, 'write'):
        f = open(f, 'wb')
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


INT_FORMAT = re.compile(br'^(?:0|-?[1-9][0-9]*)$')


def readstr(f, lead=b''):
    """Read a bencoded string. Accepts leading bytes that are already read."""
    size = int(lead + fileutil.readupto(f, b':'))
    if size < 0:
        raise ValueError('bad string size')
    return fileutil.readexactly(f, size)


def readint(f):
    """Read a bencoded integer (after leading 'i')."""
    s = fileutil.readupto(f, b'e')
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
        if c == b'e':
            return ret
        key = readstr(f, c)
        ret[key] = readany(f)


def readany(f, checkend=False):
    """Read any bencoded value.

    Will return None if next char is 'e' and checkend=True.
    """
    c = fileutil.readexactly(f, 1)
    if checkend and c == b'e':
        return None
    try:
        return {b'i':readint, b'l':readlist, b'd':readdict}[c](f)
    except KeyError:
        return readstr(f, c)


def writeany(f, obj):
    """Write any bencoded value."""
    if isinstance(obj, dict):
        f.write(b'd')
        for k in sorted(obj):
            if not isinstance(k, bytes):
                raise TypeError('dict key is not a string')
            writeany(f, k)
            writeany(f, obj[k])
        f.write(b'e')
    elif isinstance(obj, list):
        f.write(b'l')
        for x in obj:
            writeany(f, x)
        f.write(b'e')
    elif isinstance(obj, bytes):
        f.write(str2bytes(str(len(obj))) + b':' + obj)
    else:
        f.write(b'i' + str2bytes(str(obj)) + b'e')


##fp = 'c:/users/elias/desktop/1.dat'
##fp2 = 'c:/users/elias/desktop/2.dat'
##dump(fp2, load(fp))
##assert open(fp, 'rb').read() == open(fp2, 'rb').read()
