import itertools


def verify(s):
    slen = len(s)
    if slen == 10:
        return verify10(s)
    elif slen == 13:
        return verify13(s)
    else:
        raise ValueError('length must be 10 or 13')
    

def verify10(s):
    """Verify ISBN-10. Input size must be 10."""
    if len(s) != 10:
        raise ValueError('string size must be 10')
    return check10(s[:-1]) == s[-1:].upper()


def verify13(s):
    """Verify ISBN-13. Input size must be 13."""
    if len(s) != 13:
        raise ValueError('string size must be 13')
    return check13(s[:-1]) == s[-1:]


def check10(s):
    """Calculate ISBN-10 check digit. Input size must be 9."""
    if len(s) != 9:
        raise ValueError('string size must be 9')
    n = sum(i * n for i, n in itertools.izip(map(int, s), xrange(1, 10))) % 11
    return str(n) if n < 10 else 'X'


def check13(s):
    """Calculate ISBN-13 check digit. Input size must be 12."""
    if len(s) != 12:
        raise ValueError('string size must be 12')
    n = 10 - sum(i * n for i, n in
                 itertools.izip(map(int, s), itertools.cycle([1, 3]))) % 10
    if n == 10: n = 0
    return str(n)
