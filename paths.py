"""Print the PATH entries."""

from __future__ import print_function
import os
import sys
import argparse
import collections


def parse_args():
    ap = argparse.ArgumentParser(
        description='print info about PATH directories',
        epilog='Normal output (i.e. without -b) also show missing and duplicate paths')
    add = ap.add_argument
    add('-b', dest='bare', action='store_true',  # TODO: remove? too simple
        help='print only raw paths')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    items = os.environ['PATH'].split(os.path.pathsep)
    if args.bare:
        for s in items:
            print(s)
    else:
        dup_counts = collections.Counter(
            os.path.normcase(os.path.expandvars(s)) for s in items
        )
        flag = [ ' ', '*' ]
        print('mis dup path')
        print('--- --- ----')
        for s in items:
            expanded = os.path.expandvars(s)
            is_missing = not os.path.isdir(expanded)
            is_duplicate = dup_counts[os.path.normcase(os.path.expandvars(s))] > 1
            print(' {}   {}  {}'.format(
                flag[is_missing],
                flag[is_duplicate],
                s
            ))
