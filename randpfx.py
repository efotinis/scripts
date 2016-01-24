"""Prepend specified files with random number.

Useful when wishing to go through some files randomly.
"""

import argparse
import glob
import os
import random
import re
import sys

import efutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='add random number in front of file names')
    add = ap.add_argument
    add('patterns', metavar='PATT', nargs='+',
        help='glob pattern of input files')
##    add('-d', dest='include_dirs', action='store_true',
##        help='include dirs in patterns'
##    add('-D', dest='only_dirs', action='store_true',
##        help='include dirs in patterns'
    add('-u', dest='undo', action='store_true',
        help='remove previously inserted numbers')
    add('-v', dest='verbose', action='store_true',
        help='display source and destination paths')
    add('--dry-run', dest='dry_run', action='store_true',
        help='run without modifying anything')
    return ap.parse_args()


def shuffled_prefixes(count):
    """Generate 'count' prefix strings (of same length) in random order."""
    if count <= 0:
        raise ValueError('count must be > 0')
    maxwidth = len(str(count))
    nums = list(range(1, count + 1))
    random.shuffle(nums)
    for n in nums:
        yield str(n).rjust(maxwidth, '0')


def collect_paths(patterns):
    """Get all file paths matching specified globs.

    Prevents duplicates.
    Prints a warning when a pattern doesn't match anything.
    """
    abspaths_seen = set()
    for patt in args.patterns:
        matches = [s for s in glob.glob(patt) if os.path.isfile(s)]
        if not matches:
            print('no files matched "{}"'.format(patt), file=sys.stderr)
        for path in matches:
            abspath = os.path.normcase(os.path.abspath(path))
            if abspath not in abspaths_seen:
                yield path
                abspaths_seen.add(abspath)


def process(paths):
    """Generate (src,dst) for each path, adding prefix to dst."""
    prefixes = shuffled_prefixes(len(paths))
    for src, prefix in zip(paths, prefixes):
        head, tail = os.path.split(src)
        dst = os.path.join(head, prefix + '. ' + tail)
        yield src, dst


def unprocess(paths):
    """Generate (src,dst) for each path, removing prefix (if any) from dst.

    Prints warning when a path doesn't seem to have a previously added prefix.
    """
    for src in paths:
        head, tail = os.path.split(src)
        m = re.match(r'^(\d+\. )(.*)$', tail)
        if not m:
            print('no prefix in "{}"'.format(src), file=sys.stderr)
            dst = src
        else:
            dst = os.path.join(head, m.group(2))
        yield src, dst


if __name__ == '__main__':
    args = parse_args()

    paths = list(collect_paths(args.patterns))
    paths = unprocess(paths) if args.undo else process(paths)

    # just rename them
    num_ok, num_fail = 0, 0
    for src, dst in paths:
        if args.verbose:
            efutil.conout('"{}" => "{}"'.format(src, dst))
        try:
            if not args.dry_run:
                os.rename(src, dst)
            num_ok += 1
        except OSError as x:
            efutil.conerr('could not rename "{}": {}'.format(src, x))
            num_fail += 1
    print()
    print('files renamed/failed: {}/{}'.format(num_ok, num_fail))
