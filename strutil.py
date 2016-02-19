"""String utilities."""

import re


def _normalize_startend(start, end, length):
    """Convert start/end indices according to Python conventions.

    Replaces start & end with 0 & length respectively if they are None,
    and handles negative indices.
    """
    if start is None:
        start = 0
    elif start < 0:
        start += length
    if end is None:
        end = length
    elif end < 0:
        end += length
    return start, end


def findall(s, sub, start=None, end=None, overlap=False):
    """Generate offsets of all occurences of a substring."""
    start, end = _normalize_startend(start, end, len(s))
    while start <= end:
        i = s.find(sub, start, end)
        if i == -1:
            break
        yield i
        start = i + (1 if overlap else len(sub))


def rfindall(s, sub, start=None, end=None, overlap=False):
    """Generate, in reverse, offsets of all occurences of a substring."""
    start, end = _normalize_startend(start, end, len(s))
    while start <= end:
        i = s.rfind(sub, start, end)
        if i == -1:
            break
        yield i
        end = i - (1 if overlap else len(sub))


TOKENIZE_QUOTED_RX = re.compile(r'''
    "(.*?)(?:"|$)   # a quoted string (closing quote optional at EOS)
    |
    ([^\s"]+)       # a string of non-spaces and non-quotes
    ''', re.VERBOSE)


def tokenize_quoted(s):
    """Split cmdline-like string to sequence of (beg,end,text) tokens.

    beg/end: location in input (including quotes)
    text: result token (without quotes)

    Tokens are separated by whitespace, unless when quoted with '"'.
    Quoted tokens are merged with adjacent tokens.
    A missing final trailing quote is ignored.

    Examples:
        >>> f = lambda s: [tok for beg,end,tok in tokenize_quoted(s)]
        >>> f('')
        []
        >>> f('a "b" c')  # quoted and plain tokens
        ['a', 'b', 'c']
        >>> f('"a b" c')  # quote whitespace
        ['a b', 'c']
        >>> f('a"b" c')   # merged adjacent
        ['ab', 'c']
        >>> f('a b "c')   # missing trailing quote
        ['a', 'b', 'c']
        >>>
    """
    beg, end, tok = None, None, None
    for m in TOKENIZE_QUOTED_RX.finditer(s):
        part = ''.join(m.groups(''))
        if tok is not None and end == m.start():
            # merge adjacent
            end = m.end()
            tok += part
            continue
        if tok is not None:
            yield beg, end, tok
        beg, end, tok = m.start(), m.end(), part
    if tok is not None:
        yield beg, end, tok
