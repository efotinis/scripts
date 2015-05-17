"""Calculate timestamp differences."""

from __future__ import print_function
import re
import sys
import math
import argparse
import mathutil


# time format: [-][[hr:]min:]sec[.fract]
rx = re.compile(r'''
    ^\s*
    (-?)                # sign
    (?:
        (?:
            (\d+):      # hours
        )?
        (\d+):          # minutes
    )?
    (\d+)               # seconds
    (\.\d+)?            # fractional
    \s*$''', re.VERBOSE)


def timestr_to_sec(timestr):
    """Convert a time string to seconds."""
    try:
        sign, hours, minutes, seconds, fraction = rx.match(timestr).groups()
        sign = -1 if sign else 1
        hours = int(hours or '0')
        minutes = int(minutes or '0')
        seconds = int(seconds)
        fraction = float(fraction or '.0')
        return sign * (((hours * 60 + minutes) * 60) + seconds + fraction)
    except (AttributeError, ValueError):
        raise ValueError('invalid time: ' + timestr)


def sec_to_timestr(sec):
    """Convert seconds to a time string."""
    sign = ' '
    if sec < 0:
        sec = -sec
        sign = '-'
    h_m_s = mathutil.multi_divmod(sec, 60, 60)
    return sign + ('%02d:%02d:%06.3f' % h_m_s)


def parse_args():
    ap = argparse.ArgumentParser(
        description='calculate lap/total times from timestamp differences',
        epilog='input time format: [-][[hr:]min:]sec[.fract]; '
               'note that the first timestamp specified is used as the start '
               '(use 0 if needed)')
    add = ap.add_argument
    add('times', metavar='TIME', nargs='*', type=timestr_to_sec,
        help='time')
    return ap.parse_args()


def calc(a):
    """Calculate lap and total times, given 2 or more timestamps."""
    if len(a) < 1:
        raise ValueError('need 2 or more timestamps')
    a = iter(a)
    start = previous = next(a)
    for n in a:
        yield n - previous, n - start
        previous = n


if __name__ == '__main__':

    args = parse_args()

    for i, (lap, total) in enumerate(calc(args.times), 1):
        print(i, sec_to_timestr(lap), sec_to_timestr(total))
