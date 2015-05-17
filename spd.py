"""Size/time/speed calculator."""

from __future__ import print_function
import sys
import re
import argparse
import efutil
import mathutil


def size_factor(unit):
    """Convert unit char to numeric factor (e.g. 'k' -> 1024).

    If unit is empty, returns 1.    
    """
    if not unit:
        return 1
    i = 'kmgtpe'.index(unit)
    return 1 << (10 * (i + 1))


def time_unit_to_sec(s):
    """Convert a time unit to seconds.

    Currently supported: 's', 'm', 'h', 'd', 'w'
    """
    return {'s':1, 'm':60, 'h':3600, 'd':3600*24, 'w':3600*24*7}[s.lower()]


def parse_size(s):
    m = re.match(r'^(\d*\.?\d*)([kmgt])?b?$', s, re.IGNORECASE)
    if not m:
        raise ValueError
    num, unit = m.groups()
    return int(float(num) * size_factor(unit))


def parse_speed(s):
    size, time = s.split('/')
    size = parse_size(size)
    time = time_unit_to_sec(time)
    return size / float(time)


def parse_time(s):
    ret = 0
    for part in s.split(':'):
        if part:
            num, unit = part[:-1], part[-1]
            ret += int(num) * time_unit_to_sec(unit)
    return ret


def fmt_size(n):
    """Convert size to string."""
    return efutil.prettysize(n)


def fmt_time(n):
    """Convert time to string."""
    if not n:
        return '0s'
    wks, days, hrs, mins, secs = mathutil.multi_divmod(n, 7, 24, 60, 60)
    a = [(wks,'w'), (days,'d'), (hrs,'h'), (mins,'m'), (secs,'s')]
    return ':'.join(str(int(n))+u for n,u in a if n)


def fmt_speed(n, unit='s'):
    """Convert speed to string."""
    n *= float(time_unit_to_sec(unit))
    return fmt_size(n) + '/' + unit


def parse_value(s):
    """Detect value type and return it's type name and parsed value.

    Examples:
        parse_value('10kb') => ('size', 10240)
        parse_value('2m:10s') => ('time', 130)
        parse_value('4k/s') => ('speed', 4096)
    """
    if '/' in s:
        return 'speed', parse_speed(s)
    elif ':' in s:
        return 'time', parse_time(s)
    else:
        return 'size', parse_size(s)


def fmt_value(type_, val, orig_str):
    p = globals()['fmt_' + type_]
    return '%s: %s (%s)' % (type_, orig_str, p(val))


def parse_cmdline():
    value_parser = lambda s: parse_value(s) + (s,)  # append original string
    value_parser.func_name = 'Parameter'  # HACK: provide a meaningful name
                                          # for argparse error reporting
    parser = argparse.ArgumentParser(
        description='Given two of size/time/speed, calculate the third.')
    parser.add_argument('value1', metavar='VAL1', type=value_parser,
                        help='first value')
    parser.add_argument('value2', metavar='VAL2', type=value_parser,
                        help='second value.')
    parser.add_argument('-t', choices='smhdw', metavar='UNIT', default='s',
                        dest='timeunit',
                        help='time unit for speed output; use initials of: '
                        'second, minute, hour, day, week; default: "%(default)s".')
    parser.add_argument('-v', action='store_true', dest='verbose',
                        help='verbose output; includes interpreted input values')
    opt = parser.parse_args()
    if opt.value1[0] == opt.value2[0]:
        parser.error('both value types are the same ("%s")' % opt.value1[0])
    return opt


if __name__ == '__main__':
    opt = parse_cmdline()

    values = {s:None for s in 'size time speed'.split()}
    values[opt.value1[0]] = opt.value1[1]
    values[opt.value2[0]] = opt.value2[1]

    if opt.verbose:
        print(fmt_value(*opt.value1))
        print(fmt_value(*opt.value2))

    if values['size'] is None:
        print('size:', fmt_size(values['speed'] * values['time']))
    elif values['time'] is None:
        print('time:', fmt_time(values['size'] / values['speed']))
    else:
        print('speed:', fmt_speed(values['size'] / values['time'], opt.timeunit))
