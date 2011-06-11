"""Suspend the system after a specified amount of time."""

import argparse
import re
import time

import win32api
import win32security

import console_stuff
import CommonTools
import secutil


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


def pretty_time(seconds):
    """Convert seconds to 'hh:mm:ss.ss' string."""
    seconds, minutes, hours = CommonTools.splitunits(seconds, (60, 60))
    #return '%02d:%02d:%05.2f' % (hours, minutes, seconds)
    return '%02d:%02d:%02.0f' % (hours, minutes, seconds)


def wait_and_suspend(seconds):
    print 'suspend in',
    spo = console_stuff.SamePosOutput()

    STEP = 1.0

    try:
        secondsleft = round(seconds)
        while secondsleft > 0:
            spo.restore(eolclear=True)
            print ('%s ...' % pretty_time(secondsleft)),
            time.sleep(STEP)
            secondsleft -= STEP
        spo.restore(eolclear=True)
        print ('%s ...' % pretty_time(secondsleft)),
    except KeyboardInterrupt:
        print 'cancelled'
        raise SystemExit

    print 'suspending...',
    with secutil.privilege_elevation([win32security.SE_SHUTDOWN_NAME]):
        win32api.SetSystemPowerState(True, False)
    print 'resumed'


def get_args():
    ap = argparse.ArgumentParser(description='suspend after specified time', add_help=False)
    ap.add_argument('seconds', type=time_string, metavar='TIME',
                    help='time to wait before suspension; format: [Nh][:][Nm][:][Ns], where N=float')
    ap.add_argument('-?', action='help', help='this help')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    wait_and_suspend(args.seconds)
