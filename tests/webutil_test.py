import unittest

import webutil


class TestFetching(unittest.TestCase):
    URL = 'http://en.wikipedia.org/wiki/Main_Page'

    def test_wget(self):
        # also tests custom user agent, since
        # Wikipedia blocks Python's default UA
        webutil.wget(self.URL)

    def test_headers(self):
        d = webutil.headers(self.URL)
        self.assertIn('Content-Length', d)
        self.assertEqual(d['Content-Language'], 'en')


if __name__ == '__main__':
    unittest.main()
