"""Suspend/hibernate the system after a specified amount of time."""

import argparse
import time
import sys

import win32api
import win32security

import secutil
import timer


def msg(s):
    """Print timestamped message."""
    print(time.ctime(), '-', s)


def wait_and_suspend(seconds, hibernate, force):
    msg('starting timer for ' + timer.pretty_time(seconds))
    try:
        timer.countdown(seconds, 0.1, 1, 'suspend in {}')
    except KeyboardInterrupt:
        msg('canceled by user')
        return
    try:
        s = 'hibernating' if hibernate else 'suspending'
        if force:
            s += ' (forced)'
        msg(s)
        with secutil.privilege_elevation([win32security.SE_SHUTDOWN_NAME]):
            win32api.SetSystemPowerState(not hibernate, force)
    except win32api.error as x:
        msg('power state set failed: ' + str(x))
    else:
        msg('resumed')


def get_args():
    ap = argparse.ArgumentParser(description='suspend after specified time')
    ap.add_argument('seconds', type=timer.time_string, metavar='TIME', 
                    help='time to wait before suspension; ' 
                    'format: [Nh][:][Nm][:][Ns], where N=float')
    ap.add_argument('-b', dest='hibernate', action='store_true', 
                    help='hibernate instead of suspending')
    ap.add_argument('-f', dest='force', action='store_true', 
                    help='force suspend (Windows Server 2003 and Windows XP only)')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    wait_and_suspend(args.seconds, args.hibernate, args.force)
