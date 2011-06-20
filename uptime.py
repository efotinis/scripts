"""Display the system uptime."""

from __future__ import division
from __future__ import print_function

import os
import argparse

if os.name == 'nt':
    import ctypes
    import win32api
    import win32pdh

import CommonTools


UNITS = {  # unit name and conversion factor
    'y': ('years',   60*60*24*7*365),
    'n': ('months',  60*60*24*7*(365/12)),
    'w': ('weeks',   60*60*24*7),
    'd': ('days',    60*60*24),
    'h': ('hours',   60*60),
    'm': ('minutes', 60),
    's': ('seconds', 1)}
UNITS_ORDER = 'ynwdhms'


def get_windows_uptime_pdh():
    """Return the system uptime in seconds via PDH."""
    query = win32pdh.OpenQuery()
    try:
        counter = win32pdh.AddCounter(query, '\\System\\System Up Time')
        win32pdh.CollectQueryData(query)
        type_, value = win32pdh.GetFormattedCounterValue(counter, win32pdh.PDH_FMT_LARGE)
        return value
    finally:
        win32pdh.CloseQuery(query)


def get_windows_uptime_ticks():
    """Return the system uptime in seconds using the tick counter.

    On systems prior to Vista the counter resets every 49.7 days.
    """
    try:
        GetTickCount64 = ctypes.windll.kernel32.GetTickCount64
        GetTickCount64.restype = ctypes.wintypes.ctypes.c_uint64
        GetTickCount64.argtypes = []
        return GetTickCount64() / 1000.0
    except AttributeError:
        return win32api.GetTickCount() / 1000.0


def get_posix_uptime():
    """Return the system uptime in seconds.
    
    From "uptime in unix" / comp.lang.python / 19 Sep 2004.
    """
    with open('/proc/uptime') as f:
        uptime, idletime = [float(s) for s in f.read().split()]
        return uptime


def get_system_uptime(include_suspended):
    """Get the system uptime in seconds (float)."""
    if os.name == 'nt':
        if include_suspended:
            return get_windows_uptime_ticks()
        else:
            return get_windows_uptime_pdh()
    elif os.name == 'posix':
        return get_posix_uptime()
    else:
        raise RuntimeError('unsupported platform: %s' % os.name)


def parse_args():
    parser = argparse.ArgumentParser(
        description='display the system uptime',
        add_help=False)
    _add = parser.add_argument
    _add('-s', dest='include_suspended', action='store_true',
         help='include time in suspension; only used on Windows; '
         'this counter resets every 49.71 days on systems prior to Vista')
    _add('-f', dest='fixed', action='store_true',
         help='output in fixed-width notation ("DD:HH:MM:SS"); '
         'the default notation uses variable width and a letter after each unit')
    units = ', '.join('{0} ({1})'.format(c, UNITS[c][0]) for c in UNITS_ORDER)
    _add('-u', dest='unit', choices=tuple(UNITS_ORDER), metavar='UNIT',
         help=('show a single unit number; available options are: {0}; '
               'month and year values are approximated').format(units))
    _add('-d', dest='decimals', type=int, default=2, metavar='DEC',
         help='decimal places to use for single unit output; default is %(default)s')
    _add('-?', action='help', help='this help')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    uptime = get_system_uptime(args.include_suspended)

    if args.unit is not None:
        n = uptime / UNITS[args.unit][1]
        print('{0:.{1}f}'.format(n, args.decimals))
    else:
        uptime = int(round(uptime))
        seconds, minutes, hours, days = CommonTools.splitunits(uptime, (60,60,24))
        fmt = '{0:02}:{1:02}:{2:02}:{3:02}' if args.fixed else '{0}d {1}h {2}m {3}s'
        print(fmt.format(days, hours, minutes, seconds))
