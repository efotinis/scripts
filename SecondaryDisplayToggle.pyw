"""Toggle the secondary monitor adapter to the desktop."""

import windisplay
import efutil
import win32api
import win32con
import pywintypes


def errorMsg(s):
    win32api.MessageBox(0, s, efutil.scriptname(), win32con.MB_ICONEXCLAMATION)


def isMirror(dev):
    return bool(dev.StateFlags & win32con.DISPLAY_DEVICE_MIRRORING_DRIVER)

def isPrimary(dev):
    return bool(dev.StateFlags & win32con.DISPLAY_DEVICE_PRIMARY_DEVICE)

def isAttached(dev):
    return bool(dev.StateFlags & win32con.DISPLAY_DEVICE_ATTACHED_TO_DESKTOP)


def toggleAdapter(dev):
    dm = pywintypes.DEVMODEType()
    if isAttached(dev):
##        cur = wd.getMode(dev.DeviceName)
##        print('*** current mode: {}x{} at {}x{} {}-bit {}Hz'.format(
##            cur.PelsWidth, cur.PelsHeight,
##            cur.Position_x, cur.Position_y, 
##            cur.BitsPerPel, cur.DisplayFrequency))
        # NOTE: all these field flags are required, despite the MSDN doc
        dm.Fields = win32con.DM_POSITION | win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
        dm.Position_x, dm.Position_y = 0, 0
        dm.PelsWidth, dm.PelsHeight = 0, 0
    else:
        dm.Fields |= (win32con.DM_POSITION |
                      win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT |
                      win32con.DM_BITSPERPEL | win32con.DM_DISPLAYFREQUENCY)
        # these values should be configurable
        dm.Position_x, dm.Position_y = -1440, 90
        dm.PelsWidth, dm.PelsHeight = 1440, 900
        dm.BitsPerPel, dm.DisplayFrequency = 32, 60

    # NOTE: Using a single ChangeDisplaySettingsEx() call doesn't work (it
    # used to before Windows 7, but not anymore). The required steps are:
    #   1. ChangeDisplaySettingsEx(dev, mode, CDS_UPDATEREGISTRY | CDS_NORESET)
    #      for each change. This also has the added benefit of allowing multiple
    #      changes to be performed simultaneously.
    #   2. ChangeDisplaySettingsEx(None, None, 0)
    #      to actually apply the changes.
    # Using just CDS_UPDATEREGISTRY makes ChangeDisplaySettingsEx succeeded,
    # but the screen just flickers and no changes are actually performed.
    #
    # See:
    # - http://stackoverflow.com/questions/3934730/c-application-to-detach-secondary-monitor
    # - http://stackoverflow.com/questions/19643985/how-to-disable-a-secondary-monitor-with-changedisplaysettingsex

    res = win32api.ChangeDisplaySettingsEx(dev.DeviceName, dm, win32con.CDS_UPDATEREGISTRY | win32con.CDS_NORESET)
    if (res != win32con.DISP_CHANGE_SUCCESSFUL):
        errorMsg('Could not change display settings: ' + windisplay.SET_MODE_RET_STR[res])

    res = win32api.ChangeDisplaySettingsEx(None, None, 0)
    if (res != win32con.DISP_CHANGE_SUCCESSFUL):
        errorMsg('Could not finalize display settings: ' + windisplay.SET_MODE_RET_STR[res])


# get the real, non-primary adapters
devs = [d for d in windisplay.adapters()
        if not isMirror(d) and not isPrimary(d)]

devcount = len(devs)
if devcount == 0:
    errorMsg('Could not find any secondary adapters.')
elif devcount > 1:
    errorMsg('More than one secondary adapter found.')
else:
    toggleAdapter(devs[0])
