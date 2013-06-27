"""Get random subreddits."""
import sys
import time
import urllib2
import webbrowser
import argparse
import webutil


USER_AGENT = 'randit.py'
REDDIT_REQUEST_DELAY_SEC = 2
SFW_URL = 'http://random.reddit.com/'
NSFW_URL = 'http://randnsfw.reddit.com/'


def get_destination(url):
    """Get destination URL (possibly redirected)."""
    req = webutil.HeadRequest(url, headers={'User-Agent': USER_AGENT})
    resp = urllib2.urlopen(req)
    resp.close()
    return resp.url


def strip_age_check(url):
    """Remove the age verification redirect.

    Example:
        'http://www.reddit.com/r/foobar/over18?dest=%2Fr%2Ffoobar%2F'
    becomes:
        'http://www.reddit.com/r/foobar/'
    """
    return url.partition('over18?')[0]


def parse_args():
    ap = argparse.ArgumentParser(description='get random subreddits')
    add = ap.add_argument
    add('-n', dest='count', type=int, default=10,
        help='number of subreddits (default: %(default)s)')
    add('-x', dest='nsfw', action='store_true', help='get NSFW subreddits')
    add('-l', dest='launch', action='store_true',
        help='launch URL in browser instead of printing')
    add('-b', dest='batch', action='store_true',
        help='print or launch everything at once (batch)')
    args = ap.parse_args()
    if args.count < 0:
        args.count = 0
    return args


def url_generator(url, count):
    """Generate subreddit URLs from a randomizer URL."""
    for i in range(count):
        time.sleep(REDDIT_REQUEST_DELAY_SEC)
        # the additional delay caused by resolving the redirection prevents duplicates
        yield strip_age_check(get_destination(url))


if __name__ == '__main__':
    args = parse_args()
    OPEN_NEW_TAB = 2
    urls = url_generator(NSFW_URL if args.nsfw else SFW_URL, args.count)
    if args.batch:
        urls = list(urls)
    for url in urls:
        if args.launch:
            webbrowser.open(url, new=OPEN_NEW_TAB, autoraise=False)
        else:
            print url
