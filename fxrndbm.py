#!python3
"""Get random items from Firefox's Other Bookmarks menu.

NOTE: prints Unicode to the console
"""

import argparse
import contextlib
import os
import random
import re
import sqlite3
import sys

import fxdata


def parse_args():
    ap = argparse.ArgumentParser(
        description='get random items from Firefox\'s Other Bookmarks')
    add = ap.add_argument
    add('profile', nargs='?', default='default',
        help='profile name or index; default: %(default)s')
    add('-n', dest='count', type=int, default=1,
        help='maximum number of bookmarks to return; default: %(default)s')
    add('-i', dest='info', action='store_true',
        help='print number of bookmarks returned and total')
    add('-b', dest='bareoutput', action='store_true',
        help='bare output (titles only)')
    return ap.parse_args()


def main(args):
    db = fxdata.open_profile(args.profile, 'places.sqlite')
    with contextlib.closing(db):
        bm = fxdata.Bookmarks(db)
        a = list(bm.unfiled())
        total = len(a)
        if args.count < len(a):
            a = random.sample(a, args.count)
        else:
            random.shuffle(a)
        for x in a:
            x = bm.get_info(x)
            print(x.title)
            if not args.bareoutput:
                print('  ' + x.url)
                print('  added:', x.added.strftime('%Y-%m-%d %H:%M'))
                if x.tags:
                    print('  tags:', ', '.join(x.tags))
                if x.notes:
                    print('  notes:', x.notes)
                print()
        if args.info:
            print('{} out of {} links'.format(len(a), total))


if __name__ == '__main__':
    main(parse_args())
