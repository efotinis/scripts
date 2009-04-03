"""Toggle current video mode between two predefined modes."""

# 2007.02.16    created
# 2007.12.12    replaced messy code to get/set mode with Display module;
#               added MessageBox for errors
# 2009.02.05    replaced Display module with windisplay

import os, sys
import win32api, win32con
import windisplay


def getMode():
    return windisplay.getDevMode(windisplay.getMode())


def setMode(mode):
    return windisplay.setMode(None, mode, win32con.CDS_UPDATEREGISTRY)


mode1 = (1024, 768, 32, 85)
mode2 = (1152, 864, 32, 85)

newMode = mode1 if getMode()[:2] != mode1[:2] else mode2
ret = setMode(newMode)

if ret != win32con.DISP_CHANGE_SUCCESSFUL:
    msg = windisplay.SET_MODE_RET_STR.get(ret, 'Unknown error (%d).' % ret)
    title = os.path.basename(sys.argv[0])
    icon = win32con.MB_ICONEXCLAMATION if ret > 0 else win32con.MB_ICONERROR
    win32api.MessageBox(0, msg, title, icon)
