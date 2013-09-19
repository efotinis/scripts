"""Lock the desktop and power down the monitor."""

import time
import monitorutil
import dllutil
from ctypes.wintypes import BOOL

LockWorkStation = dllutil.winfunc('user32', 'LockWorkStation', BOOL, ())

time.sleep(1)
monitorutil.turnoffmonitor()
LockWorkStation()
