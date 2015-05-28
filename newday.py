"""Test for new day.

Keeps a log of the last time it was called and exits with 0 only when a new
day is detected. The hour on which the day changes can be shifted from the
default (midnight).

Useful for scripts that shouldn't run more than once a day.
"""

import argparse
import datetime
import sys


def parse_args():
    ap = argparse.ArgumentParser(
        description='check for new day')
    add = ap.add_argument
    add('-m', dest='midnight_shift', type=int, default=0,
        help='midnight shift in hours; can be used to change the day change '
        'threshold to something other than 00:00; useful for night owls; '
        'for example, 4 means that the day changes at 04:00; default is 0; '
        'range: -23 to 23')
    add('logfile', help='log file path')
    args = ap.parse_args()
    if not -23 <= args.midnight_shift <= 23:
        ap.error('midnight shift out of range')
    return args


class Log(object):
    def __init__(self, path):
        self.path = path
    def get(self):
        """Get stored date or None on error."""
        try:
            with open(self.path) as f:
                return datetime.date(*map(int, f.read().split('-')))
        except (OSError, ValueError, TypeError):
            return None
    def set(self, date):
        """Store date."""
        with open(self.path, 'w') as f:
            f.write(str(date))


if __name__ == '__main__':
    args = parse_args()

    now = datetime.datetime.utcnow()
    shift = datetime.timedelta(hours=args.midnight_shift)
    curdate = (now - shift).date()

    log = Log(args.logfile)
    lastdate = log.get()
    changed = lastdate is None or curdate != lastdate
    if changed:
        log.set(curdate)
    else:
        sys.exit(1)
