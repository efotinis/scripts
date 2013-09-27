"""Web utilities.

tags: web
compat: 2.7+, 3.3+
platform: any
"""

try:
    import urllib2 as urllib_req
except ImportError:
    import urllib.request as urllib_req


def _req_headers(user_headers):
    """Merge user headers dict with module's default headers."""
    headers = {
        # override Python's default UA, which gets blocked by some sites
        'User-Agent': 'webutil.py/0.1',
        # this should be implied, but some sites require it
        'Accept': '*/*',
    }
    headers.update(user_headers)
    return headers


def wget(url, headers={}):
    """Get a Web resource. Useful for the interactive interpreter."""
    req = urllib_req.Request(url, headers=_req_headers(headers))
    return urllib_req.urlopen(req).read()


class HeadRequest(urllib_req.Request):
    """HEAD request.

    Source: http://stackoverflow.com/questions/107405/how-do-you-send-a-head-http-request-in-python/2070916#2070916

    Note: some sites deliberately reject HEAD requests, often due to
    the dynamic nature of the content being served.

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
    res = urllib_req.urlopen(HeadRequest(url, headers=_req_headers(headers)))
    res.close()
    return res.info()
