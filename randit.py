"""Go to random subreddits."""

import os
import re
import sys
import time
import urllib2
import urlparse
import webbrowser
import argparse
import webutil
import contextlib


USER_AGENT = 'randit.py'
REDDIT_REQUEST_DELAY_SEC = 2
SFW_URL = 'http://random.reddit.com/'
NSFW_URL = 'http://randnsfw.reddit.com/'
DEFAULT_HISTORY_PATH = '%AppData%\\randit-seen.log'
NAME_RX = re.compile(r'^https?://www.reddit.com/r/(.*)/$')


def get_destination(url):
    """Get destination URL (possibly redirected)."""
    req = webutil.HeadRequest(url, headers={'User-Agent': USER_AGENT})
    resp = urllib2.urlopen(req)
    resp.close()
    return resp.url


def strip_age_check(url):
    """Remove the age verification redirect.

    Example:
        'http://www.reddit.com/over18?dest=http%3A%2F%2Fwww.reddit.com%2Fr%2Ffoobar%2F'
    becomes:
        'http://www.reddit.com/r/foobar/'
    """
    s = urlparse.urlsplit(url).query
    return urlparse.parse_qs(s)['dest'][0]


def parse_args():
    ap = argparse.ArgumentParser(
        description='visit random subreddits',
        epilog='previously returned subreddit names are kept in "%s"' %
            DEFAULT_HISTORY_PATH
    )
    add = ap.add_argument
    add('-n', dest='count', type=int, default=5,
        help='number of subreddits (default: %(default)s)')
    add('-x', dest='nsfw', action='store_true', help='get NSFW subreddits')
    add('-p', dest='print_', action='store_true',
        help='print URLs instead of launching in browser')
    add('-i', dest='incremental', action='store_true',
        help='produce results incrementally; by default everything is output '
        'at once')
    add('-H', dest='nohistory', action='store_true',
        help='ignore previously returned subreddits; this will prevent '
        'nondeterministic delays caused by retrying')
    args = ap.parse_args()
    if args.count < 0:
        args.count = 0
    return args


def get_name(url):
    """Extract the subreddit name from its URL."""
    m = NAME_RX.match(url)
    if not m:
        raise ValueError('could not find sub name in "{}"'.format(url))
    return m.group(1)


def url_generator(nsfw, count, history):
    """Generate subreddit URLs.

    history is a set-like object that keeps track of already generated subs.
    """
    url = NSFW_URL if nsfw else SFW_URL
    while count > 0:
        time.sleep(REDDIT_REQUEST_DELAY_SEC)
        # the additional delay caused by resolving the redirection prevents duplicates
        s = get_destination(url)
        if nsfw:
            s = strip_age_check(s)
        name = get_name(s)
        if name in history:
            print >>sys.stderr, 'skipping already seen:', name
            continue
        yield s
        history.add(name)
        count -= 1


class History(object):
    """Keep track of a set of strings.

    Use in a with statement to persist data in a simple text file.
    """

    def __init__(self, path):
        self.path = path
        self.data = None

    def __enter__(self):
        self.data = set()
        try:
            with open(self.path) as f:
                self.data.update(s.rstrip('\n') for s in f)
        except IOError:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.path, 'w') as f:
            for s in self.data:
                print >>f, s
        self.data = None

    def add(self, s):
        self.data.add(s)

    def __contains__(self, s):
        return s in self.data


class DummyHistory(object):
    """Dummy version of History class.

    Always appears empty and doesn't store anything.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def add(self, s):
        pass

    def __contains__(self, s):
        return False


if __name__ == '__main__':
    args = parse_args()
    history = DummyHistory() if args.nohistory else \
              History(os.path.expandvars(DEFAULT_HISTORY_PATH))
    with history:
        OPEN_NEW_TAB = 2
        urls = url_generator(args.nsfw, args.count, history)
        if not args.incremental:
            urls = list(urls)
        for url in urls:
            if args.print_:
                print url
            else:
                webbrowser.open(url, new=OPEN_NEW_TAB, autoraise=False)
