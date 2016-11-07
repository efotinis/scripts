#!python2
"""Lock the desktop and power down the monitor."""

import time
import monitorutil
import dllutil
from ctypes.wintypes import BOOL

LockWorkStation = dllutil.winfunc('user32', 'LockWorkStation', BOOL, ())


def lockdown():
    monitorutil.turnoffmonitor()
    LockWorkStation()


if __name__ == '__main__':
    time.sleep(1)
    lockdown()
