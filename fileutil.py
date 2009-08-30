"""File related utilities."""

import os


def fsize(f):
    """Size of an open file (must be seekable)."""
    orgpos = f.tell()
    try:
        f.seek(0, os.SEEK_END)
        return f.tell()
    finally:
        f.seek(orgpos)


def eofdistance(f):
    """Distance to EOF; may be negative if pointer is past EOF."""
    orgpos = f.tell()
    try:
        f.seek(0, os.SEEK_END)
        return f.tell() - orgpos
    finally:
        f.seek(orgpos)


def readexactly(f, size):
    """Read an exact number of bytes from a file."""
    ret = f.read(size)
    if len(ret) != size:
        raise IOError('unexpected end of data')
    return ret


def readupto(f, delim, keep=False):
    """Read from a file up to a delimiter byte.

    The delimiter will be consumed, but it won't appear in the result,
    unless 'keep' is True.
    """
    ret = ''
    while True:
        c = readexactly(f, 1)
        if c == delim:
            if keep:
                ret += c
            return ret
        ret += c

    
