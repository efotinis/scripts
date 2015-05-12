"""Path utilities."""

import os
import itertools


def namegen_winshell(fn, start=2):
    """Generate successive filenames like Windows Explorer.

    Example: 'stem.ext', 'stem (2).ext', 'stem (3).ext', etc.
    """
    yield fn
    stem, ext = os.path.splitext(fn)
    for i in itertools.count(start):
        yield '{0:s} ({1:d}){2:s}'.format(stem, i, ext)


def namegen_dotnum(fn, start=1, width=3):
    """Generate successive filenames with a dot+number.

    Example: 'stem.ext', 'stem.001.ext', 'stem.002.ext', etc.
    """
    yield fn
    stem, ext = os.path.splitext(fn)
    for i in itertools.count(start):
        yield '{0:s}.{1:0{2}d}{3:s}'.format(stem, i, width, ext)


try:
    _STRTYPES = (str, unicode)
except NameError:
    _STRTYPES = (str,)


def get_unique_file(path, gen=None):
    """Generate a unique, non-existing file path.

    'gen' is a generator of base names (stem+ext) accepting the original base name.
    It can be a string to match the X part of one of the 'namegen_X' generators in
    this module. If it's None, a default will be selected based on the host system.

    NOTE: Subject to race conditions.
    """
    if gen is None:
        gen = 'winshell' if os.name == 'nt' else 'dotnum'
    if isinstance(gen, _STRTYPES):
        gen = globals()['namegen_' + gen]
    parent, base = os.path.split(path)
    for s in gen(base):
        path = os.path.join(parent, s)
        if not os.path.exists(path):
            return path


def set_ext(p, ext):
    """Replace a path's extension."""
    return os.path.splitext(p)[0] + ext


def split_all(s):
    """Split all elements of a path."""
    a = []
    while True:
        head, tail = os.path.split(s)

        # get tail, unless when s==os.sep*N, where split() returns (s,'')
        if tail or head != s:
            a += [tail]

        # done; input path was absolute
        if head == s:
            a += [head]
            break

        # done; input path was not absolute
        if not head:
            break

        s = head
    a.reverse()
    return a


##assert split_all('') == ['']
##assert split_all('/') == ['/']
##assert split_all('//') == ['//']
##assert split_all('a') == ['a']
##assert split_all('a/') == ['a', '']
##assert split_all('/a') == ['/', 'a']
##assert split_all('a/b') == ['a', 'b']
##assert split_all('a/b/') == ['a', 'b', '']
##assert split_all('/a/b/') == ['/', 'a', 'b', '']
##assert split_all('c:/a/b/') == ['c:/', 'a', 'b', '']
