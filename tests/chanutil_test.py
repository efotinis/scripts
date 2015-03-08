from __future__ import print_function
import sys
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse
import unittest

from bs4 import BeautifulSoup

import webutil
import chanutil


def get_sample_thread():
    """Get the URL of a random thread.

    Currently gets the first thread from the recent images in 4chan's frontpage.
    """
    scheme = 'https:'
    html = webutil.wget(scheme + '//www.4chan.org/')
    bsoup = BeautifulSoup(html)
    recent_post_url = bsoup.find('div', id='recent-images').a['href']
    recent_thread_url = urlparse.urldefrag(recent_post_url)[0]
    if not urlparse.urlsplit(recent_thread_url).scheme:
        recent_thread_url = scheme + recent_thread_url
    return recent_thread_url


class BaseUrlTest(unittest.TestCase):
    """Base for test classes needing sample URLs.
    
    Suggested in http://stackoverflow.com/a/8276384
    """
    real_url = get_sample_thread()
    assert '/res/' in real_url
    bad_url = real_url.replace('/res/', '/bogus/')
    bad_domain = 'http://www.example.com/'


class TestUrlParsing(BaseUrlTest):

    def test_real_url(self):
        chanutil.get_page_info(self.real_url)

    def test_bad_url(self):
        with self.assertRaises(chanutil.UrlError):
            chanutil.get_page_info(self.bad_url)

    def test_bad_domain(self):
        with self.assertRaises(chanutil.UrlError):
            chanutil.get_page_info(self.bad_domain)


class TestImages(BaseUrlTest):

    def test_get_images(self):
        _, _, _, image_gen = chanutil.get_page_info(self.real_url)
        bs = BeautifulSoup(webutil.wget(self.real_url))
        list(image_gen(bs))


if __name__ == '__main__':
    # TODO: we should test all supported domains
    # TODO: we should somehow find the expected number of images and
    #   compare it to what we get (probably by scrap)
    unittest.main()
