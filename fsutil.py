"""File system (and path) utilities."""

import contextlib

import binutil


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
    """Windows DWORD attributes string.Formatter

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


