#!python3
"""Display recursive file/dir/byte counts of directories."""

import argparse
import os
import re

import efutil
import wildcard


def parse_args():
    UNITS = 'bkmgtpe'
    ap = argparse.ArgumentParser(
        description='prints the total subdirs/files/bytes of directories')

    add = ap.add_argument

    add('-u', dest='unit', choices=UNITS, default='b',
        help='the outsize size unit; default: %(default)s')
    add('-d', dest='decs', type=int, default=0,
        help='output decimal digits (ignored for bytes); default: %(default)s')
    add('-G', dest='nogrouping', action='store_true',
        help='disable digit grouping')
    add('-b', dest='bareoutput', action='store_true',
        help='bare output (no header)')
    add('dirs', nargs='+', metavar='DIR',
        help='source directory path; wildcards allowed (in non-parent parts only)')

    args = ap.parse_args()

    args.decs = min(max(0, args.decs), 10)
    args.unit = 1024 ** UNITS.index(args.unit)
    if args.unit == 1:
        args.decs = 0

    return args


def deep_dir(root):
    """Total dirs, files and bytes in the specified dir (recursively).

    Prints errors to STDERR.
    """
    def report_error(x):
        efutil.conerr(str(x))
    def get_size(path):
        try:
            return os.path.getsize(path)
        except OSError as x:
            report_error(x)
            return 0
    root = os.path.abspath(root)
    dirs, files, bytes = 0, 0, 0
    for p,d,f in os.walk(root, onerror=report_error):
        dirs += len(d)
        files += len(f)
        bytes += sum(get_size(os.path.join(p, s)) for s in f)
    return dirs, files, bytes


def match_dirs(pattern):
    """Generate dir paths from a '[PATH\]WILDCARD' pattern.

    Prints errors to STDERR.
    """
    pattern = os.path.normpath(pattern.strip())
    head, tail = os.path.split(pattern)
    if not wildcard.iswild(tail):
        yield pattern
        return
    name_rx = wildcard.build(tail or '*')
    try:
        names = os.listdir(head or '.')
    except OSError as x:
        efutil.conerr(str(x))
        return
    for s in names:
        path = os.path.join(head, s)
        if os.path.isdir(path) and name_rx.match(s):
            yield path


if __name__ == '__main__':
    args = parse_args()
    try:
        if not args.bareoutput:
            print('{:>10} {:>10} {:>15} {}'.format('dirs', 'files', 'size', 'name'))
            print('{:>10} {:>10} {:>15} {}'.format('----', '-----', '----', '----'))
        fmtstr = '{:10,} {:10,} {:15,.{}f} {}'
        if args.nogrouping:
            fmtstr = fmtstr.replace(',', '')

        for pattern in args.dirs:
            matched_something = False
            for path in match_dirs(pattern):
                matched_something = True
                if not os.path.isdir(path):
                    efutil.conerr('not a directory: "{}"'.format(path))
                    continue
                dirs, files, bytes = deep_dir(path)
                size = bytes / args.unit
                efutil.conout(fmtstr.format(dirs, files, size, args.decs, path))
            if not matched_something:
                efutil.conerr('nothing matched pattern: "{}"'.format(pattern))

    except KeyboardInterrupt:
        efutil.conout('cancelled')
