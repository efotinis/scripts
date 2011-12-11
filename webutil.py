"""Web utilities."""

try:
    # Python 2.x
    import urllib2 as _urllib
except ImportError:
    # Python 3.x
    import urllib.request as _urllib


def wget(url):
    """Read a Web resource.

    Added to the interactive interpreter via PYTHONSTARTUP.
    """
    # add user agent, because some sites (e.g. Wikipedia)
    # forbid access to unknown/blank user-agents
    req = _urllib.Request(url, headers={'User-Agent':'Opera'})
    return _urllib.urlopen(req).read()
