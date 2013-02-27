"""Rename files using source and target list files."""

import os
import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='rename using src/dst list files')
    add = parser.add_argument
    add('srclist', metavar='SRC', help='source list')
    add('dstlist', metavar='DST', help='destination list')
    add('-d', dest='dirpath', default='.', help='base dir path')
    add('-v', dest='verbose', action='store_true',
        help='verbose output; shows all renamed files')
    args = parser.parse_args()
    if not os.path.isdir(args.dirpath):
        parser.error('invalid base dir: "%s"' % args.dirpath)
    if not os.path.isfile(args.srclist):
        parser.error('invalid source list: "%s"' % args.srclist)
    if not os.path.isfile(args.dstlist):
        parser.error('invalid destination list: "%s"' % args.dstlist)
    return args


if __name__ == '__main__':
    args = parse_args()
    src = [s.rstrip('\n') for s in open(args.srclist)]
    dst = [s.rstrip('\n') for s in open(args.dstlist)]
    if len(src) != len(dst):
        sys.exit('source and destination lists have different sizes')
    if args.dirpath != os.path.curdir:
        src = [os.path.join(args.dirpath, s) for s in src]
        dst = [os.path.join(args.dirpath, s) for s in dst]
    count_ok, count_failed = 0, 0
    for fn1, fn2 in zip(src, dst):
        try:
            os.rename(fn1, fn2)
            if args.verbose:
                print '"%s" => "%s"' % (fn1, fn2)
            count_ok += 1
        except OSError as x:
            print >>sys.stderr, 'ERROR: could not rename "%s" to "%s"; %s' % (fn1, fn2, x)
            count_failed += 1
    print 'files renamed:', count_ok
    print 'failed:', count_failed
