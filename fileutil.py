"""File related utilities."""

import os
import contextlib


@contextlib.contextmanager
def preserve_pos(f, offset=None, whence=os.SEEK_SET):
    """Context manager to preserve (and optionally set) a file's position."""
    orgpos = f.tell()
    if offset is not None:
        f.seek(offset, whence)
    try:
        yield
    finally:
        f.seek(orgpos)


def fsize(f):
    """Size of an open file (must be seekable)."""
    with preserve_pos(f, 0, os.SEEK_END):
        return f.tell()


def eofdistance(f):
    """Distance to EOF (negative if pointer is past EOF)."""
    return fsize(f) - f.tell()


def readexactly(f, size):
    """Read an exact number of bytes from a file."""
    ret = f.read(size)
    if len(ret) != size:
        raise EOFError
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
