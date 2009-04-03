import os, re


def iswild(s):
    """Test if a string contains wildcards (*?)."""
    return '*' in s or '?' in s


def build(wildcard, casesens=False):
    """Create a regexp to match a wildcard."""
    rx = ''
    for c in wildcard:
        if c == '*':
            rx += '.*'
        elif c == '?':
            rx += '.'
        else:
            rx += re.escape(c)
    return re.compile('^' + rx + '$',
                      0 if casesens else re.IGNORECASE)


def test(wildcard, s, casesens=False):
    """Perform a wildcard (str or regexp) test."""
    if isinstance(wildcard, basestring):
        wildcard = build(wildcard, casesens)
    return wildcard.match(s) is not None


def listdir(wildcard, dir, casesens=False):
    """Return a dir listing filtered by a wildcard (str or regexp)."""
    if isinstance(wildcard, basestring):
        wildcard = build(wildcard, casesens)
    return [s for s in os.listdir(dir) if test(wildcard, s)]


class Wildcard:
    def __init__(self, s, casesens=False):
        """A wildcard object."""
        self.rx = build(s, casesens)
    def test(self, s):
        return test(self.rx, s, casesens)
    def listdir(self, dir):
        return listdir(self.rx, dir, casesens)
    