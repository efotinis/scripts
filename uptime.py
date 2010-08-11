"""Display the system uptime."""

from __future__ import division
from __future__ import print_function

import argparse
import wintime
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


parser = argparse.ArgumentParser(
    description='Display the system uptime.',
    epilog='On systems prior to Vista, the uptime counter is reset every 49.7 days.',
    add_help=False)
_add = parser.add_argument
_add('-f', dest='fixed', action='store_true',
     help='Output in fixed width notation ("DDD:HH:MM:SS"). '
     'The default notation uses variable width and a letter after each unit.')
units = ', '.join('{0} ({1})'.format(c, UNITS[c][0]) for c in UNITS_ORDER)
_add('-u', dest='unit', choices=tuple(UNITS_ORDER), metavar='UNIT',
     help=('Show a single unit number. Available options are: {0}. '
           'Month and year values are approximated.').format(units))
_add('-d', dest='decimals', type=int, default=2, metavar='DEC',
     help='Decimal places to use for single unit output. Default is %(default)s.')
_add('-?', action='help', help='This help.')
opt = parser.parse_args()

uptime = wintime.get_tick_count(bits=64, fallback=True) / 1000

if opt.unit is not None:
    n = uptime / UNITS[opt.unit][1]
    print('{0:.{1}f}'.format(n, opt.decimals))
else:
    uptime = int(round(uptime))
    seconds, minutes, hours, days = CommonTools.splitunits(uptime, (60,60,24))
    fmt = '{0:03}:{1:02}:{2:02}:{3:02}' if opt.fixed else '{0}d {1}h {2}m {3}s'
    print(fmt.format(days, hours, minutes, seconds))
