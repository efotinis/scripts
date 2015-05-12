"""Move files to subdirs in equal-sized groups."""

from __future__ import division
import os
import argparse
import math
import fsutil
import CommonTools


def parse_args():
    ap = argparse.ArgumentParser(
        description='scatter files to subdirs',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add = ap.add_argument
    add('-d', dest='dirpath', default='.', help='source directory')
    add('-s', dest='start', type=int, default=0, help='start number for subdir names')
    add('count', type=int, nargs='?', default=10, help='number of subdirs to create')
    args = ap.parse_args()
    if args.count <= 0:
        ap.error('count must be > 0')
    if args.start < 0:
        ap.error('start must be >= 0')
    return args


def group_sizes(count, total):
    """Split 'total' to 'count' groups as evenly as possible.

    This means that all groups should be equal, apart from the last,
    which may be smaller.
    """
    group_size = int(math.ceil(total / count))
    while total > 0:
        n = min(group_size, total)
        yield n
        total -= n


if __name__ == '__main__':
    args = parse_args()
    with fsutil.preserve_cwd(args.dirpath):
        fnames = [s for s in os.listdir(u'.') if os.path.isfile(s)]
        for i, count in enumerate(group_sizes(args.count, len(fnames)), args.start):
            a, fnames = fnames[:count], fnames[count:]
            dest_dir = str(i)
            if not os.path.exists(dest_dir):
                try:
                    os.mkdir(dest_dir)
                except OSError as x:
                    CommonTools.conerr('could not create "%s"; %s' % (dest_dir, x))
                    continue
            for s in a:
                try:
                    os.rename(s, os.path.join(dest_dir, s))
                except OSError as x:
                    CommonTools.conerr('could not move "%s"; %s' % (s, x))
