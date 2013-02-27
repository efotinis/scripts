"""Calculate the difference between two times."""

from __future__ import print_function
import re
import sys
import math
import argparse
import CommonTools
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
    sign = ''
    if sec < 0:
        sec = -sec
        sign = '-'
    h_m_s = mathutil.multi_divmod(sec, 60, 60)
    return sign + ('%02d:%02d:%06.3f' % h_m_s)


def parse_args():
    ap = argparse.ArgumentParser(
        description='calculate the difference between two times',
        epilog='input time format: [-][[hr:]min:]sec[.fract]')
    add = ap.add_argument
    add('-v', dest='verbose', action='store_true', help='verbose output: include the (normalized) input times')
    add('start_t', metavar='START', type=timestr_to_sec, help='start time')
    add('end_t', metavar='END', type=timestr_to_sec, help='end time')
    return ap.parse_args()


if __name__ == '__main__':

    args = parse_args()

    diff = args.end_t - args.start_t
    sign = ''
    if diff < 0:
        diff = -diff
        sign = '-'
    if args.verbose:
        print('%s ... %s -> ' % (
                sec_to_timestr(args.start_t),
                sec_to_timestr(args.end_t)),
            end='')
    print('%s%s' % (sign, sec_to_timestr(diff)))
