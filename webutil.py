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
    # add headers to disguise ourselves from some servers 
    # that block non-browser access (i.e. Wikipedia)
    # and specify that we accept everything
    req = _urllib.Request(url, headers={
        'User-Agent': 'Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.16',
        'Accept': '*/*',
    })
    return _urllib.urlopen(req).read()


class HeadRequest(_urllib.Request):
    """HEAD request.

    Source: http://stackoverflow.com/questions/107405/how-do-you-send-a-head-http-request-in-python/2070916#2070916

    >>> url = 'http://skeptoid.com/audio/skeptoid-4246.mp3'
    >>> res = urllib2.urlopen(HeadRequest(url))
    >>> res.geturl()
    'http://hw.libsyn.com/p/9/1/6/9166f8eb735db475/skeptoid-4246.mp3?sid=6888a47b5a4c85fce757fbd6c5d5a057&l_sid=17974&l_eid=&l_mid=2462743'
    >>> print res.info()
    Date: Wed, 23 Feb 2011 09:33:53 GMT
    Connection: close
    Accept-Ranges: bytes
    ETag: "1298228777"
    Last-Modified: Sun, 20 Feb 2011 19:06:17 GMT
    Cache-Control: max-age=86400
    Content-Length: 9696736
    Content-Type: audio/mpeg
    X-HW: 1298453633.cm038a4
    """
    def get_method(self):
        return "HEAD"


def headers(url, headers={}):
    """Get headers dict of web resource."""
    res = _urllib.urlopen(HeadRequest(url, headers=headers))
    res.close()
    return res.info().dict
