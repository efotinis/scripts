"""Print the PATH entries."""

import os
import sys
import argparse
import collections


def parse_args():
    ap = argparse.ArgumentParser(
        description='print PATH directories',
        epilog='flags shown: "*" non-existing, "!" douplicate')
    add = ap.add_argument
    add('-b', dest='bare', action='store_true',
        help='print only paths')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    items = os.environ['PATH'].split(os.path.pathsep)
    dup_counts = collections.Counter(os.path.normcase(s) for s in items)
    if args.bare:
        for s in items:
            print s
    else:
        for s in items:
            flags = ''
            flags += '*' if not os.path.isdir(s) else ' '
            flags += '!' if dup_counts[os.path.normcase(s)] > 1 else ' '
            print flags, s
