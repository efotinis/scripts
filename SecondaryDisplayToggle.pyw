"""Toggle the secondary monitor adapter to the desktop.

2009.01.01  created
"""
import windisplay
import CommonTools
import win32api
import win32con
import pywintypes


def errorMsg(s):
    win32api.MessageBox(0, s, CommonTools.scriptname(), win32con.MB_ICONEXCLAMATION)


def isMirror(dev):
    return bool(dev.StateFlags & win32con.DISPLAY_DEVICE_MIRRORING_DRIVER)

def isPrimary(dev):
    return bool(dev.StateFlags & win32con.DISPLAY_DEVICE_PRIMARY_DEVICE)

def isAttached(dev):
    return bool(dev.StateFlags & win32con.DISPLAY_DEVICE_ATTACHED_TO_DESKTOP)


def toggleAdapter(dev):
    dm = pywintypes.DEVMODEType()
    # this isn't needed, because ChangeDisplaySettingsEx gets it as a param
    #dm.DeviceName = dev.DeviceName
    if isAttached(dev):
        dm.Fields = (win32con.DM_POSITION |  # DM_POSITION is required
                     win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT)
        dm.PelsWidth, dm.PelsHeight = 0, 0
    else:
        dm.Fields |= (win32con.DM_POSITION |
                      win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT |
                      win32con.DM_BITSPERPEL | win32con.DM_DISPLAYFREQUENCY)
        # set arbitrary mode (here the display is placed left of the primary
        # with their top sides aligned)
        dm.Position_x, dm.Position_y = -1024, 0
        dm.PelsWidth, dm.PelsHeight = 1024, 768
        dm.BitsPerPel, dm.DisplayFrequency = 32, 75
    res = win32api.ChangeDisplaySettingsEx(dev.DeviceName, dm, win32con.CDS_UPDATEREGISTRY)
    if (res != win32con.DISP_CHANGE_SUCCESSFUL):
        errorMsg('Could not change display settings: ' + windisplay.SET_MODE_RET_STR[res])


# get the real, non-primary adapters
devs = [d for d in windisplay.adapters() if not (isMirror(d) or isPrimary(d))]

devcount = len(devs)
if devcount == 0:
    errorMsg('Could not find any secondary adapters.')
elif devcount > 1:
    errorMsg('More than one secondary adapter found.')
else:
    toggleAdapter(devs[0])
