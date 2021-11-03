"""Lock the desktop and power down the monitor."""

import argparse
import time
import monitorutil
import dllutil
from ctypes.wintypes import BOOL

LockWorkStation = dllutil.winfunc('user32', 'LockWorkStation', BOOL, ())


def PositiveFloat(s):
    n = float(s)
    return n if n >= 0 else 0


def parse_args():
    ap = argparse.ArgumentParser(
        description='lock desktop and power down monitor'
    )
    ap.add_argument('-d', dest='delay', type=PositiveFloat, default=0.1,
        help='delay in seconds; may be needed to properly power down monitor; '
            'default: %(default)s')
    return ap.parse_args()


def lockdown():
    monitorutil.turnoffmonitor()
    LockWorkStation()


if __name__ == '__main__':
    args = parse_args()
    time.sleep(args.delay)
    lockdown()
