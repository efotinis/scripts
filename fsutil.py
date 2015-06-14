"""File system (and path) utilities."""

import os
import contextlib

import binutil
import wildcard


@contextlib.contextmanager
def preserve_cwd(path=None):
    """Context manager to preserve (and optionally set) the current directory."""
    orgpath = os.getcwd()
    if path is not None:
        os.chdir(path)
    try:
        yield
    finally:
        os.chdir(orgpath)


def win_attrib_str(n):
    """Windows DWORD attributes string.

    Returns string with fixed len of 32, using spaces for missing/unknown flags.
    Only documented/unreserved flags are returned:
        0x00000001  FILE_ATTRIBUTE_READONLY             R
        0x00000002  FILE_ATTRIBUTE_HIDDEN               H
        0x00000004  FILE_ATTRIBUTE_SYSTEM               S
        0x00000008  (undocumented)
        0x00000010  FILE_ATTRIBUTE_DIRECTORY            D
        0x00000020  FILE_ATTRIBUTE_ARCHIVE              A
        0x00000040  FILE_ATTRIBUTE_DEVICE (reserved)
        0x00000080  FILE_ATTRIBUTE_NORMAL               N
        0x00000100  FILE_ATTRIBUTE_TEMPORARY            T
        0x00000200  FILE_ATTRIBUTE_SPARSE_FILE          X
        0x00000400  FILE_ATTRIBUTE_REPARSE_POINT        P
        0x00000800  FILE_ATTRIBUTE_COMPRESSED           C
        0x00001000  FILE_ATTRIBUTE_OFFLINE              O
        0x00002000  FILE_ATTRIBUTE_NOT_CONTENT_INDEXED  I
        0x00004000  FILE_ATTRIBUTE_ENCRYPTED            E
        0x00008000  (undocumented)
        0x00010000  FILE_ATTRIBUTE_VIRTUAL              V
    """                                            
    return binutil.flagchars(n, 32, 'RHS DA NTXPCOIE V')


def os_walk_rel(top, topdown=True, onerror=None, followlinks=False):
    """os.walk variant returning relative dir paths instead of full parent.

    The first iteration will always return '' for the top dir, so joining
    the relative path with the top will match the original parent.
    """
    for parent, dirs, files in os.walk(top, topdown, onerror, followlinks):
        rel = parent[len(top):].lstrip(os.path.sep)
        yield rel, dirs, files


def _getall(topdir, files=True, dirs=False, recurse=True):
    """Get all item paths under 'topdir'.

    'files'/'dirs' denote whether to return the respective items.
    'recurse' causes subdirs to be scanned as well.
    """
    if recurse:
        for parent, dirnames, filenames in os.walk(topdir):
            if dirs:
                for s in dirnames:
                    yield os.path.join(parent, s)
            if files:
                for s in filenames:
                    yield os.path.join(parent, s)
    else:
        for s in os.listdir(topdir):
            path = os.path.join(topdir, s)
            if os.path.isdir(path):
                if dirs:
                    yield path
            else:
                if files:
                    yield path


def _mask_test(mask):
    """Create a function to test a path against a wildcard mask.

    If mask is None, everything matches.
    """
    if mask is not None:
        mask = wildcard.Wildcard(mask)
    def tester(path):
        return mask is None or \
               mask.test(os.path.basename(path))
    return tester


def _ext_test(ext):
    """Create a function to test a path against an extension.

    ext can be a single extension or a sequence of them.
    If it is None, everything matches.
    """
    if ext is not None:
        if isinstance(ext, str):
            ext = set([os.path.normcase(ext)])
        else:
            ext = set(os.path.normcase(s) for s in ext)
    def tester(path):
        return ext is None or \
               os.path.normcase(os.path.splitext(path)[1]) in ext
    return tester


def find(topdir, files=True, dirs=False, recurse=True, ext=None, mask=None):
    """Get all item paths under 'topdir' matching the specified parameters."""
    ext = _ext_test(ext)
    mask = _mask_test(mask)
    for path in _getall(topdir, files, dirs, recurse):
        if ext(path) and mask(path):
            yield path
