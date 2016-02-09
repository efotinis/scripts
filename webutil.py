"""Web utilities.

tags: web
compat: 2.7+, 3.3+
platform: any
"""

import six

import contextlib
import pickle
import re
if six.PY2:
    from urllib2 import urlopen as urlopen_, Request
    urlopen = lambda req: contextlib.closing(urlopen_(req))
else:
    from urllib.request import urlopen, Request

try:
    import chardet
except ImportError:
    chardet = None


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


# based on requests.utils.get_encodings_from_content()
# (note that requests 3 will stop using tag detection)
HTML5_RX = re.compile(six.b(r'<meta.*?charset=["\']*(.+?)["\'>]'), re.IGNORECASE)
HTML_RX = re.compile(six.b(r'<meta.*?content=["\']*;?charset=(.+?)["\'>]'), re.IGNORECASE)
XML_RX = re.compile(six.b(r'^<\?xml.*?encoding=["\']*(.+?)["\'>]'))


def deduce_encoding(content, info):
    """Guess missing encoding (mainly for textual responses).

    Steps:
        1. If specified in HTTP headers, return that
        2. If non-text, return None
        3. If HTML/XML, look in tags
        4. use chardet (if available) or fallback to 'latin1'
    """
    # Content-Type HTTP header
    cset = info.getparam('charset') if six.PY2 else info.get_content_charset()
    if cset:
        return cset

    # return nothing if non-text
    maintype = info.getmaintype() if six.PY2 else info.get_content_maintype()
    if maintype != 'text':
        return None

    # snif HTML/XML tags (top 1K of content only)
    subtype = info.getsubtype() if six.PY2 else info.get_content_subtype()
    top_content = content[:1024]
    if subtype == 'html':
        m = HTML5_RX.search(top_content) or HTML_RX.search(top_content)
    elif subtype == 'xml':
        m = XML_RX.search(top_content)
    else:
        m = None
    if m:
        return m.group(1).decode('ascii')

    # other text; detect or fallback to ISO-8859-1
    return chardet.detect(content)['encoding'] if chardet else 'latin1'


def wget(url, headers={}):
    """Get a Web resource. Useful for the interactive interpreter."""
    req = Request(url, headers=_req_headers(headers))
    with urlopen(req) as resp:
        content = resp.read()
        enc = deduce_encoding(content, resp.info())
    return content.decode(enc) if enc else content


class UrlCache(object):
    """Cache URL resources."""
    
    def __init__(self, path):
        self.path = path
        try:
            with open(self.path, 'rb') as f:
                self.store = pickle.load(f)
        except IOError:
            self.store = {}

    def save(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self.store, f, pickle.HIGHEST_PROTOCOL)

##    def load(self, path):
##        pass
##
##    def save(self, path):
##        pass
##
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def wget(self, url, headers={}):
        key = (url, tuple((k,headers[k]) for k in sorted(headers.keys())))
        try:
            data = self.store[key]
        except KeyError:
            data = self.store[key] = wget(url, headers)
        return data


class HeadRequest(Request):
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
    """Get headers of web resource."""
    req = HeadRequest(url, headers=_req_headers(headers))
    with urlopen(req) as resp:
        return resp.info()
