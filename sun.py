"""Calculate sun event times for a particular location."""

from __future__ import print_function
import argparse
import astral
import datetime
import sys


EVENTS = 'dawn sunrise noon sunset dusk'.split()
EVENT_FLAGS = 'drnsu'


def parse_args():
    ap = argparse.ArgumentParser(
        description='calculate sun times')
    add = ap.add_argument
    add('location', help='location to get information about '
        '("City" or "City/Region")')
    add('-e', dest='events', default=['sunrise', 'sunset'], type=events_param,
        help='events to display; one or more of: "d" (dawn), "r" (sunrise), '
        '"n" (noon), "s" (sunset), "u" (dusk); use "*" for all; default is "rs"')
    add('-d', dest='date', metavar='YYYY-MM-DD', type=date_param,
        default=datetime.date.today(), 
        help='date to calculate times for; default is current')
    add('-n', dest='daycount', type=int, default=1, 
        help='number of days to output; default is 1')
    add('-u', dest='utctimes', action='store_true',
        help='output UTC instead of local times')
    add('-g', dest='googlegeo', action='store_true',
        help='use Google Maps API for location information; by default '
        'a built-in database with major world cities is used')
    return ap.parse_args()


def date_param(s):
    y, m, d = s.split('-', 2)
    return datetime.date(int(y), int(m), int(d))


def events_param(s):
    if '*' in s:
        return EVENTS[:]
    else:
        return [name for name, flag in zip(EVENTS, EVENT_FLAGS) if flag in s]


def dates(start, count):
    """Generate 'count' datetime.date objects beginning from 'start'."""
    day = datetime.timedelta(days=1)
    for n in range(count):
        yield start
        start += day


if __name__ == '__main__':
    args = parse_args()

    try:
        geo = astral.GoogleGeocoder if args.googlegeo else astral.AstralGeocoder
        ast = astral.Astral(geo)
        loc = ast[args.location]
    except astral.AstralError as x:
        sys.exit(x)
    except KeyError as x:
        # strip quotes, since astral inits KeyError with a message instead of a key
        s = str(x)
        if s[:1] + s[-1:] in ('""', "''"):
            s = s[1:-1]
        sys.exit(s)

    print('{:.<12} {}'.format('location ', loc))
    try:    
        for date in dates(args.date, args.daycount):
            print(date)
            sun = loc.sun(date=date, local=not args.utctimes)
            for e in args.events:
                print('{:.<12} {}'.format(e + ' ', sun[e]))
    except astral.AstralError as x:
        print(x, file=sys.stderr)
