"""Simple timer with alert."""

import re
import sys
import time
import argparse

import win32api
import win32con
import win32console

import CommonTools
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
    seconds, minutes, hours = CommonTools.splitunits(seconds, (60, 60))
    secsize = 2 + decimals + int(decimals > 0)
    return '%02d:%02d:%0*.*f' % (hours, minutes, secsize, decimals, seconds)


def countdown(seconds, step=1.0, decimals=0, format='%s'):
    spo = console_stuff.SamePosOutput()
    while seconds > step:
        spo.restore(eolclear=True)
        sys.stdout.write(format % pretty_time(seconds, decimals))
        time.sleep(step)
        seconds -= step
    time.sleep(seconds)
    spo.restore(eolclear=True)
    #sys.stdout.write(pretty_time(0))


def countdown_bigecho(font, seconds, step=1.0, decimals=0, format='%s'):
    for i in range(font.height):
        print
    cout = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    info = cout.GetConsoleScreenBufferInfo()
    pos = info['CursorPosition']
    attrib = info['Attributes']
    pos.Y -= font.height
    disp_width = len(format % pretty_time(seconds, decimals))
    disp_width = disp_width * font.width + (disp_width - 1) * font.spacing
    rect = win32console.PySMALL_RECTType(pos.X, pos.Y, pos.X + disp_width - 1, pos.Y + font.height - 1)
    scroll_pos = win32console.PyCOORDType(pos.X, pos.Y - font.height)

    while seconds > step:
        cout.SetConsoleCursorPosition(pos)
        font.uprint(format % pretty_time(seconds, decimals))
        time.sleep(step)
        seconds -= step
    time.sleep(seconds)
    cout.SetConsoleCursorPosition(pos)
    cout.ScrollConsoleScreenBuffer(rect, rect, scroll_pos, u' ', attrib)


def alert():
    """Make a beep to notify the user."""
    win32api.MessageBeep(win32con.MB_ICONINFORMATION)


def parse_args():
    parser = argparse.ArgumentParser(
        description='start an alert timer',
        add_help=False)
    _add = parser.add_argument
    _add('seconds', type=time_string, metavar='[[h:]m:]s', help='timer duration')
    _add('-b', dest='bigecho', action='store_true', help='show large characters')
    _add('-?', action='help', help='this help')
    return parser.parse_args()


BIG_FONT = '''
XXX  X  XXX XXX X X XXX XXX XXX XXX XXX         
X X XX    X   X X X X   X     X X X X X      X  
X X  X  XXX XXX XXX XXX XXX  X  XXX XXX         
X X  X  X     X   X   X X X X   X X   X      X  
XXX XXX XXX XXX   X XXX XXX X   XXX XXX  X      
'''


if __name__ == '__main__':
    args = parse_args()
    if args.bigecho:
        FULL_BLOCK = unichr(0x2588)
        font = bigecho.Font('0123456789.:', BIG_FONT.replace('X', FULL_BLOCK), 3, weight=2)
        countdown_bigecho(font, args.seconds, 0.05, 2)
    else:
        countdown(args.seconds, 0.1, 1)
    alert()

    
