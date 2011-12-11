"""ASCII map printer."""

import sys
import argparse


def parse_args():
    ap = argparse.ArgumentParser(
        description='ASCII map printer',
        add_help=False)
    add = ap.add_argument
    add('-n', dest='rowsize', action='store_const', const=16, default=32,
        help='narrow ouput (%(const)d chars/line); default is %(default)d')
    add('-b', dest='bareoutput', action='store_true',
        help='bare output (no row/column labels)')
    add('-?', action='help', help='this help')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    # header
    if not args.bareoutput:
        headerfmt = '%01x' if args.rowsize <= 16 else '%02x'
        headers = map(''.join, zip(*[headerfmt % i for i in range(args.rowsize)]))
        for s in headers:
            print '   ' + s
        print '   ' + '-' * args.rowsize

    # rows
    for i in range(32, 256, args.rowsize):
        if not args.bareoutput:
            sys.stdout.write('%02x|' % i)
        print ''.join(chr(c) for c in range(i, i+args.rowsize))
