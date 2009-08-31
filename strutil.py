"""String utilities."""


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


