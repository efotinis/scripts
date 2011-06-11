"""Display the system uptime."""

from __future__ import division
from __future__ import print_function

import os
import argparse
import CommonTools

if os.name == 'nt':
    # try loading in order: wintime, win32api, ctypes
    try:
        import wintime
    except ImportError:
        wintime = None
        try:
            import win32api
        except ImportError:
            win32api = None
            import ctypes


UNITS = {  # unit name and conversion factor
    'y': ('years',   60*60*24*7*365),
    'n': ('months',  60*60*24*7*(365/12)),
    'w': ('weeks',   60*60*24*7),
    'd': ('days',    60*60*24),
    'h': ('hours',   60*60),
    'm': ('minutes', 60),
    's': ('seconds', 1)}
UNITS_ORDER = 'ynwdhms'


def system_uptime():
    """Get the system uptime in seconds (float)."""
    if os.name == 'nt':
        # note that 32-bit values wrap around at approx. 49.71 days
        if wintime:
            # Vista+ supports a 64-bit value
            return wintime.get_tick_count(bits=64, fallback=True) / 1000
        elif win32api:
            return win32api.GetTickCount() / 1000
        else:
            return ctypes.windll.kernel32.GetTickCount() / 1000
    elif os.name == 'posix':
        # from comp.lang.python "uptime in unix" (19 Sep 2004)
        with open('/proc/uptime') as f:
            uptime, idletime = [float(s) for s in f.read().split()]
            return uptime
    else:
        raise RuntimeError('unsupported platform: %s' % os.name)


def parse_args():
    parser = argparse.ArgumentParser(
        description='display the system uptime',
        epilog='on certain systems (e.g. Windows prior to Vista), '
               'the uptime counter is reset every 49.71 days',
        add_help=False)
    _add = parser.add_argument
    _add('-f', dest='fixed', action='store_true',
         help='output in fixed width notation ("DDD:HH:MM:SS"); '
         'the default notation uses variable width and a letter after each unit')
    units = ', '.join('{0} ({1})'.format(c, UNITS[c][0]) for c in UNITS_ORDER)
    _add('-u', dest='unit', choices=tuple(UNITS_ORDER), metavar='UNIT',
         help=('show a single unit number; available options are: {0}; '
               'month and year values are approximates').format(units))
    _add('-d', dest='decimals', type=int, default=2, metavar='DEC',
         help='decimal places to use for single unit output; default is %(default)s')
    _add('-?', action='help', help='this help')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    uptime = system_uptime()

    if args.unit is not None:
        n = uptime / UNITS[args.unit][1]
        print('{0:.{1}f}'.format(n, args.decimals))
    else:
        uptime = int(round(uptime))
        seconds, minutes, hours, days = CommonTools.splitunits(uptime, (60,60,24))
        fmt = '{0:03}:{1:02}:{2:02}:{3:02}' if args.fixed else '{0}d {1}h {2}m {3}s'
        print(fmt.format(days, hours, minutes, seconds))
