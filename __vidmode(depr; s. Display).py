# 2007.08.10  created
# 2007.12.12  docstrings & minor edits; added modeflags & modestr;
#             added demo code
#
#  TODO:
#   - ren module to Display or WinDisplay
#   - ren getDispDev to getDevices, getDispSettings to getSettings
#        OR
#     make Devices, Settings iterators
#
#


import win32api, win32con


EDS_RAWMODE = 2  # getDispSettings (EnumDisplaySettingsEx) flag


def _enumhelper(func, dev=None):
    """Collect a list of objects from an enumerating function.

    The function must accept a device (or None) and an index.
    """
    ret = []
    try:
        i = 0
        while True:
            ret += [func(dev, i)]
            i += 1
    except win32api.error:
        pass
    return ret


def getDispDev(dev=None):
    enum = lambda dev, i: win32api.EnumDisplayDevices(dev, i)
    return _enumhelper(enum, dev)


def getDispSettings(dev=None, flags=0):
    enum = lambda dev, i: getSettings(win32api.EnumDisplaySettingsEx(dev, i, flags))
    return _enumhelper(enum, dev)


def getCurDispSettings(dev=None):
    """Get the display settings currently in effect."""
    return getSettings(win32api.EnumDisplaySettings(
        dev, win32con.ENUM_CURRENT_SETTINGS))
    

def getRegDispSettings(dev=None):
    """Get the display settings stored in the registry."""
    return getSettings(win32api.EnumDisplaySettings(
        dev, win32con.ENUM_REGISTRY_SETTINGS))
    

def changeDispSettings(dev=None, mode=None, flags=0):
    """Change mode.

    'mode' can be either a PyDEVMODE or a tuple of settings (as returned
    by getSettings). """
    if mode is not None and type(mode) != pywintypes.DEVMODEType:
        pass
    #win32api.ChangeDisplaySettingsEx(


def getSettings(dm):
    """Get the relevant members from a DEVMODE object."""
    return (dm.PelsWidth, dm.PelsHeight, dm.BitsPerPel, dm.DisplayFrequency,
        dm.DisplayFlags)


# flags returned when dev=None
adapterflags = {
    win32con.DISPLAY_DEVICE_ATTACHED_TO_DESKTOP: 'deskAttach',
    win32con.DISPLAY_DEVICE_MULTI_DRIVER: '(multiDrv)',
    win32con.DISPLAY_DEVICE_PRIMARY_DEVICE: 'primDev',
    win32con.DISPLAY_DEVICE_MIRRORING_DRIVER: 'mirrDrv',
    win32con.DISPLAY_DEVICE_VGA_COMPATIBLE: 'vgaCompat',
    win32con.DISPLAY_DEVICE_REMOVABLE: 'removable',
    win32con.DISPLAY_DEVICE_MODESPRUNED: 'nodesPrun',
    win32con.DISPLAY_DEVICE_REMOTE: '(remote)',
    win32con.DISPLAY_DEVICE_DISCONNECT: '(disconn)'}


# flags returned when dev!=None
monitorflags = {
    1: 'active', # DISPLAY_DEVICE_ACTIVE
    2: 'attached'} # DISPLAY_DEVICE_ATTACHED


# DEVMODE flags;
# note that wingdi.h says DM_GRAYSCALE and DM_INTERLACED are no longer valid
modeflags = {
    win32con.DM_GRAYSCALE: 'grayscale',  # commented out from Win32 header
    win32con.DM_INTERLACED: 'interlaced',  # commented out from Win32 header
    4: 'textmode',  # DMDISPLAYFLAGS_TEXTMODE
    }
    

def flagstr(flags, names):
    """Return a string from flags"""
    a = []
    for i in range(32):
        mask = 2**i
        if flags & mask and mask in names:
            a += [names[mask]]
            flags &= ~mask
    if flags:
        a += ['0x%08x' % flags]
    return ', '.join(a)


def modestr(a):
    """Return a string from a tuple of width, height, bpp and
    optionally freq and flags."""
    s = '%d*%d %d-bit' % a[:3]
    if len(a) > 3:
        s += ' %dHz' % a[3]
    if len(a) > 4 and a[4]:
        s += ' ' + flagstr(a[4], modeflags)
    return s


if __name__ == '__main__':
    print 'Adapters and devices:'
    for x in getDispDev(None):
        print '-'*70
        print '  name:', x.DeviceName
        print 'string:', x.DeviceString
        print ' state:', flagstr(x.StateFlags, adapterflags)
        print '    id:', x.DeviceID
        for y in getDispDev(x.DeviceName):
            print '\t', '-'*20
            print '\t', '  name:', y.DeviceName
            print '\t', 'string:', y.DeviceString
            print '\t', ' state:', flagstr(y.StateFlags, monitorflags)
            print '\t', '    id:', y.DeviceID
    print
    print 'Supported resolutions in default adapter'
    print '(! = unsupported by monitor):'
    monres = set(dm[:2] for dm in getDispSettings())
    rawres = set(dm[:2] for dm in getDispSettings(None, EDS_RAWMODE))
    for xy in sorted(rawres):
        print '  %d*%d %s' % (xy[0], xy[1], ' ' if xy in monres else '!')
    print
    print 'Current mode:', modestr(getCurDispSettings())
    print 'Registry mode:', modestr(getRegDispSettings())
