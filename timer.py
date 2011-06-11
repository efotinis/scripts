"""Simple timer with alert."""

import sys
import time
import re
import argparse
import win32api
import win32con


# regex for [[H:]M:]S
HHMMSS_RX = re.compile(r'''
    (?:
        (?:
            (\d+):  # hours
        )?
        (\d+):      # minutes
    )?
    (\d+)           # seconds
''', re.VERBOSE)


def alert():
    """Make a beep to notify the user."""
    win32api.MessageBeep(win32con.MB_ICONINFORMATION)


def wait(sec):
    """Wait a number of seconds (can be fractional)."""
    endtime = time.time() + sec
    for interval in (60,1,0.05):
        while sec > interval and time.time() < endtime:
            time.sleep(interval)
            sec -= interval

def testwait(sec):
    """Wait for a numner of seconds and return requested
    and elapsed time."""
    t = time.time()
    wait(sec)
    t = time.time() - t
    return sec, t


def parsetime(s):
    """Parse any of the supported time format
    and return result in seconds. Raise ValueError on error.

    Currently supported formats:
    - [[hh:]mm:]ss
    """
    mo = HHMMSS_RX.match(s)
    if not mo:
        raise ValueError('invalid time format "%s"' % s)
    h,m,s = (int(s or 0) for s in mo.groups())
    return ((h * 60) + m) * 60 + s


##ap = argparse.ArgumentParser(description='alarm/timer functions', add_help=False)
##_add = ap.add_argument
##_add('-?', action='help', help='this help')
##print ap.parse_args()


if __name__ == '__main__':
    args = sys.argv[1:]
    if '/?' in args:
        print 'Starts a timer.'
        print 'Usage: TIMER [[hours:]minutes:]seconds'
        return
    if len(args) != 1:
        raise SystemExit('exactly 1 argument is required')
    try:
        seconds = parsetime(args[0])
    except ValueError, x:
        raise SystemExit(str(x))
    wait(seconds)
    alert()
