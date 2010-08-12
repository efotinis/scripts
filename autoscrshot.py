"""Automatically and periodically save a system display screenshot."""

from __future__ import print_function

import re
import sys
import time
import datetime
import argparse
from PIL import ImageGrab


def bbox(s):
    """Parse a bounding box parameter ('l,t,r,b')."""
    a = map(int, s.split(','))
    if len(a) != 4:
        raise ValueError
    return a


def parse_args():
    """Parse cmdline."""
    parser = argparse.ArgumentParser(
        description='Take periodic snapshots of the system display.',
        add_help=False)

    _add = parser.add_argument

    _add(dest='interval', type=int, metavar='SEC',
         help='number of seconds between screenshots')
    _add(dest='outfile', metavar='OUTPUT',
         help='destination file; can contain the following replacement parameters: '
              '$T (local time), $N (0-based index), $$ (dollar sign)')
    _add('-f', dest='format', metavar='FMT',
         help='image format; default depends on output extension')
    _add('-b', dest='bbox', type=bbox, metavar='BOX',
         help='screen coordinates to capture; default is the whole screen')
    _add('-c', dest='count', type=int, metavar='NUM', 
         help='maximum number of snapshots; if omitted, Ctrl-C can be used to exit')
    _add('-?', action='help', help='this help')

    args = parser.parse_args()

    # range checks
    if args.interval <= 0:
        parser.error('seconds must be > 0')
    if args.count is not None and args.count <= 0:
        parser.error('snapshot count must be > 0')

    return args


def replace_vars(m, index, timestamp):
    """Replace $ vars."""
    s = m.group(1)
    if s == '$':
        return s
    elif s == 'N':
        return '{0:06d}'.format(index)
    elif s == 'T':
        return timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]
    else:
        print('invalid replacement char: "{0}"'.format(s), file=sys.stderr)


if __name__ == '__main__':
    try:
        args = parse_args()
        var_index, var_time = 0, None

        while True:
            if args.count is None:
                pass
            elif args.count > 0:
                args.count -= 1
            else:
                break

            var_time = datetime.datetime.now()
            repl = lambda m: replace_vars(m, index=var_index, timestamp=var_time)
            outname = re.sub(r'\$(.)', repl, args.outfile)
            var_index += 1

            grabtime = time.time()

            im = ImageGrab.grab(bbox=args.bbox)
            im.save(outname, format=args.format)

            sleeptime = args.interval - (time.time() - grabtime)
            if sleeptime > 0:
                time.sleep(sleeptime)

    except KeyboardInterrupt:
        pass
