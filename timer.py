"""Simple timer with alert."""

import re
import sys
import time
import argparse
import contextlib

import win32api
import win32con
import win32console

import mathutil
import console_stuff
import bigecho
import wintime


def time_string(s):
    """Convert a time string to float seconds.

    Format: "Nh[:]Nm[:]Ns". All elements are optional, but at least one must be present.

    Examples:
    >>> time_string('10s')
    10.0
    >>> time_string('1m10s')
    70.0
    >>> time_string('5m:10s')
    310.0
    >>> time_string('2.5h')
    9000.0
    """
    m = re.match(r'^(?:([0-9.]+)h)?:?(?:([0-9.]+)m)?:?(?:([0-9.]+)s)?$', s.lower())
    if not m or m.groups() == (None, None, None):
        raise ValueError('invalid time string: "%s"' % s)
    hours, minutes, seconds = [float(s or '0') for s in m.groups()]
    return ((hours * 60) + minutes) * 60 + seconds


def pretty_time(seconds, decimals=0):
    """Convert seconds to 'hh:mm:ss.ss' string."""

    # round the seconds to the requested output decimals before divmod
    # to prevent cases where the seconds of the output string gets rounded
    # incorrectly (e.g. pretty_time('.3333h', 0) -> '00:19:60')
    seconds = round(seconds, decimals)

    hours, minutes, seconds = mathutil.multi_divmod(seconds, 60, 60)
    secsize = 2 + decimals + int(decimals > 0)
    return '%02d:%02d:%0*.*f' % (hours, minutes, secsize, decimals, seconds)


def timer(seconds, step):
    """Countdown seconds and yield remaining time in every step.

    A final value of 0 is always returned.

    Although the intermediate steps may not be extremely accurate, the total
    time is guaranteed to be accurate to the millisecond, regardless of the
    step size.

    Suspending the system during countdown is not supported.
    """
    cur = wintime.get_tick64()
    end = cur + int(seconds * 1000)
    while cur < end:
        seconds_left = (end - cur) / 1000.0
        yield seconds_left
        if step < seconds_left:
            time.sleep(step)
            cur = wintime.get_tick64()
        else:
            time.sleep(seconds_left)
            yield 0.0
            return


def countdown(seconds, step=1.0, decimals=0, fmt='{}'):
    """Countdown display.

    fmt can be used to output a custom string with the counter.
    """
    spo = console_stuff.SamePosOutput()
    try:
        for seconds in timer(seconds, step):
            spo.restore(eolclear=True)
            sys.stdout.write(fmt.format(pretty_time(seconds, decimals)))
            sys.stdout.flush()  # needed in Py3
    finally:
        spo.restore(eolclear=True)
        #sys.stdout.write(pretty_time(0))


def countdown_bigecho(font, seconds, step=1.0, decimals=0, fmt='{}'):
    """Countdown display using a bigecho font.

    fmt can be used to output a custom string with the counter.
    """
    sys.stdout.write('\n' * font.height)  # allocate vertical space
    cout = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    info = cout.GetConsoleScreenBufferInfo()
    pos = info['CursorPosition']
    attrib = info['Attributes']
    pos.Y -= font.height
    disp_width = len(fmt.format(pretty_time(seconds, decimals)))
    disp_width = disp_width * font.width + (disp_width - 1) * font.spacing
    rect = win32console.PySMALL_RECTType(pos.X, pos.Y, pos.X + disp_width - 1, pos.Y + font.height - 1)
    scroll_pos = win32console.PyCOORDType(pos.X, pos.Y - font.height)

    try:
        for seconds in timer(seconds, step):
            cout.SetConsoleCursorPosition(pos)
            font.uprint(fmt.format(pretty_time(seconds, decimals)))
    finally:
        cout.SetConsoleCursorPosition(pos)
        cout.ScrollConsoleScreenBuffer(rect, rect, scroll_pos, u' ', attrib)


def parse_args():
    parser = argparse.ArgumentParser(
        description='simple countdown timer; can cancel with Ctrl-C',
        epilog='time display is erased on exit')
    _add = parser.add_argument
    _add('seconds', type=time_string, metavar='TIME', help='timer duration; examples: '
         '"10s", "1m10s", "5m:10s", "2.5h"')
    _add('-l', dest='large', action='store_true', help='show large characters')
    _add('-b', dest='beeponce', action='store_true', help='beep once on completion')
    _add('-B', dest='beeploop', action='store_true', help='beep continuously after completion')
    _add('-d', dest='decimals', type=int, default=1, help='second fractional digits; default: %(default)s')
    _add('-c', dest='cancelerror', action='store_true', help='exit with error if canceled prematurely')
    _add('-a', dest='attributes', type=int, help='output color attributes (0..255)')
    _add('-f', dest='format', default='{}', help='formatting string to display timer with; default: %(default)s')
    args = parser.parse_args()
    args.decimals = min(max(args.decimals, 0), 3)
    if args.attributes is not None and (args.attributes < 0 or args.attributes > 255):
        parser.error('attributes value must be 0..255')
    return args


BIG_FONT = (
    'XXX  X  XXX XXX X X XXX XXX XXX XXX XXX         \n'
    'X X XX    X   X X X X   X     X X X X X      X  \n'
    'X X  X  XXX XXX XXX XXX XXX  X  XXX XXX         \n'
    'X X  X  X     X   X   X X X X   X X   X      X  \n'
    'XXX XXX XXX XXX   X XXX XXX X   XXX XXX  X      \n'
)


@contextlib.contextmanager
def StdoutAttribute(n=None):
    """Context manager for preserving STDOUT text attributes."""
    out = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    org = out.GetConsoleScreenBufferInfo()['Attributes']
    if n is not None:
        out.SetConsoleTextAttribute(n)
    try:
        yield
    finally:
        out.SetConsoleTextAttribute(org)


@contextlib.contextmanager
def StdoutCursor(size=None, visible=None):
    """Context manager for preserving STDOUT cursor size/visibility."""
    out = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    orgSize, orgVisible = out.GetConsoleCursorInfo()
    assert visible is not None
    if size is not None or visible is not None:
        out.SetConsoleCursorInfo(
            size or orgSize,
            visible if visible is not None else orgVisible
        )
    try:
        yield
    finally:
        out.SetConsoleCursorInfo(orgSize, orgVisible)


if __name__ == '__main__':
    args = parse_args()

    try:
        step = 10.0**(-args.decimals) / 2  # half the smallest displayable value
        step = min(max(step, 0.01), 1)  # not too small (CPU intensive) or too large (at least 1 sec accurate)
        with StdoutCursor(visible=False), StdoutAttribute(args.attributes):
            if args.large:
                FULL_BLOCK = u'\u2588'
                bitmaps = bigecho.chars_from_string(BIG_FONT.replace('X', FULL_BLOCK), 3, 1)
                font = bigecho.Font('0123456789.:', bitmaps, 3, 5, weight=2)
                countdown_bigecho(font, args.seconds, step, args.decimals, args.format)
            else:
                countdown(args.seconds, step, args.decimals, args.format)
    except KeyboardInterrupt:
        if args.cancelerror:
            sys.exit('timer canceled')
        else:
            sys.exit()

    if args.beeploop:
        try:
            while True:
                win32api.MessageBeep(win32con.MB_ICONINFORMATION)
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    elif args.beeponce:
        win32api.MessageBeep(win32con.MB_ICONINFORMATION)
