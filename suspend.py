"""Suspend the system after a specified amount of time."""

import argparse
import time
import sys

import win32api
import win32security

import console_stuff
import CommonTools
import secutil
import timer


def wait_and_suspend(seconds):
    try:
        timer.countdown(seconds, 0.1, 1, 'suspend in {}')
    except KeyboardInterrupt:
        sys.exit('canceled by user')
    print 'suspending...',
    with secutil.privilege_elevation([win32security.SE_SHUTDOWN_NAME]):
        win32api.SetSystemPowerState(True, False)
    print 'resumed'


def get_args():
    ap = argparse.ArgumentParser(description='suspend after specified time', add_help=False)
    ap.add_argument('seconds', type=timer.time_string, metavar='TIME',
                    help='time to wait before suspension; format: [Nh][:][Nm][:][Ns], where N=float')
    ap.add_argument('-?', action='help', help='this help')
    return ap.parse_args()


if __name__ == '__main__':
    args = get_args()
    wait_and_suspend(args.seconds)
