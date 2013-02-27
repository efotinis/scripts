"""Simple timer with alert."""

import re
import sys
import time
import argparse

import win32api
import win32con
import win32console

import mathutil
import console_stuff
import bigecho


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
    hours, minutes, seconds = mathutil.multi_divmod(seconds, 60, 60)
    secsize = 2 + decimals + int(decimals > 0)
    return '%02d:%02d:%0*.*f' % (hours, minutes, secsize, decimals, seconds)


def countdown(seconds, step=1.0, decimals=0, fmt='{}'):
    """Countdown display.

    fmt can be used to output a custom string with the counter.
    """
    spo = console_stuff.SamePosOutput()
    try:
        while seconds > step:
            spo.restore(eolclear=True)
            sys.stdout.write(fmt.format(pretty_time(seconds, decimals)))
            time.sleep(step)
            seconds -= step
        time.sleep(seconds)
    finally:
        spo.restore(eolclear=True)
        #sys.stdout.write(pretty_time(0))


def countdown_bigecho(font, seconds, step=1.0, decimals=0, fmt='{}'):
    """Countdown display using a bigecho font.

    fmt can be used to output a custom string with the counter.
    """
    for i in range(font.height):
        print
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
        while seconds > step:
            cout.SetConsoleCursorPosition(pos)
            font.uprint(fmt.format(pretty_time(seconds, decimals)))
            time.sleep(step)
            seconds -= step
        time.sleep(seconds)
    finally:
        cout.SetConsoleCursorPosition(pos)
        cout.ScrollConsoleScreenBuffer(rect, rect, scroll_pos, u' ', attrib)


def parse_args():
    parser = argparse.ArgumentParser(
        description='simple countdown timer',
        add_help=False)
    _add = parser.add_argument
    _add('seconds', type=time_string, metavar='TIME', help='timer duration; examples: '
         '"10s", "1m10s", "5m:10s", "2.5h"')
    _add('-l', dest='large', action='store_true', help='show large characters')
    _add('-b', dest='beeponce', action='store_true', help='beep once on completion')
    _add('-B', dest='beeploop', action='store_true', help='beep continuously after completion')
    _add('-d', dest='decimals', type=int, default=1, help='second fractional digits; default: %(default)s')
    _add('-?', action='help', help='this help')
    args = parser.parse_args()
    args.decimals = min(max(args.decimals, 0), 3)
    return args


BIG_FONT = '''
XXX  X  XXX XXX X X XXX XXX XXX XXX XXX         
X X XX    X   X X X X   X     X X X X X      X  
X X  X  XXX XXX XXX XXX XXX  X  XXX XXX         
X X  X  X     X   X   X X X X   X X   X      X  
XXX XXX XXX XXX   X XXX XXX X   XXX XXX  X      
'''

if __name__ == '__main__':
    args = parse_args()
    
    try:
        timer_completed = False
        step = 10.0**(-args.decimals) / 2  # half the smallest displayable value
        step = min(max(step, 0.01), 1)  # not too small (CPU intensive) or too large (at least 1 sec accurate)
        if args.large:
            FULL_BLOCK = unichr(0x2588)
            bitmaps = bigecho.chars_from_string(BIG_FONT.replace('X', FULL_BLOCK), 3, 1)
            font = bigecho.Font('0123456789.:', bitmaps, 3, 5, weight=2)
            countdown_bigecho(font, args.seconds, step, args.decimals)
        else:
            countdown(args.seconds, step, args.decimals)
        timer_completed = True

        if args.beeploop:
            while True:
                win32api.MessageBeep(win32con.MB_ICONINFORMATION)
                time.sleep(1)
        elif args.beeponce:
            win32api.MessageBeep(win32con.MB_ICONINFORMATION)

    except KeyboardInterrupt:
        if not timer_completed:
            sys.exit('timer canceled by user')
