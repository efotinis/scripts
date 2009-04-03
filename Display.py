# 2007.08.10    created
# 2007.12.12    replaced enum funcs with iterators;
#               added demo code and dispChangeMsg
#

import win32api, win32con, pywintypes


EDS_RAWMODE = 2  # Settings (EnumDisplaySettingsEx) flag


# Note that 0 is success, >0 is warning (DISP_CHANGE_RESTART) and <0 is error.
dispChangeMsg = {
    win32con.DISP_CHANGE_SUCCESSFUL: 'The settings change was successful.',
    win32con.DISP_CHANGE_RESTART: 'The computer must be restarted for the graphics mode to work.',
    win32con.DISP_CHANGE_FAILED: 'The display driver failed the specified graphics mode.',
    win32con.DISP_CHANGE_BADMODE: 'The graphics mode is not supported.',
    win32con.DISP_CHANGE_NOTUPDATED: 'Unable to write settings to the registry.',
    win32con.DISP_CHANGE_BADFLAGS: 'An invalid set of flags was passed in.',
    win32con.DISP_CHANGE_BADPARAM: 'An invalid parameter was passed in. This can include an invalid flag or combination of flags.',
    win32con.DISP_CHANGE_BADDUALVIEW: 'The settings change was unsuccessful because the system is DualView capable.',
}


class _Iter:
    """Base iterator class.

    Derived classes must provide an 'enum' function accepting
    an index and returning something, or raising win32api.error.
    """
    def __init__(self):
        self.index = 0
    def __iter__(self):
        return self
    def next(self):
        try:
            ret = self.enum(self.index)
            self.index += 1
            return ret
        except win32api.error:
            raise StopIteration


class Devices(_Iter):
    def __init__(self, dev=None):
        """Iterator for adapters (dev=None) or monitors (dev!=None)."""
        _Iter.__init__(self)
        self.dev = dev
    def enum(self, i):
        return win32api.EnumDisplayDevices(self.dev, i)


class Settings(_Iter):    
    def __init__(self, dev=None, flags=0):
        """Iterator returning PyDEVMODE objects."""
        _Iter.__init__(self)
        self.dev = dev
        self.flags = flags
    def enum(self, i):
        return win32api.EnumDisplaySettingsEx(self.dev, i, self.flags)


def currentSettings(dev=None):
    """The display settings currently in effect."""
    return win32api.EnumDisplaySettings(dev,
        win32con.ENUM_CURRENT_SETTINGS)
    

def registrySettings(dev=None):
    """The display settings stored in the registry."""
    return win32api.EnumDisplaySettings(dev,
        win32con.ENUM_REGISTRY_SETTINGS)
    

def changeSettings(dev=None, mode=None, flags=0):
    """Change display settings.

    Mode is either a DEVMODE or a tuple of width. height, bpp and freq.
    """
    if mode is not None and type(mode) != pywintypes.DEVMODEType:
        mode = buildMode(mode)
    return win32api.ChangeDisplaySettingsEx(dev, mode, flags)


def resetSettings(dev=None):
    """Reset settings to those stored in registry."""
    return changeSettings(dev)


# flags returned when dev=None
adapterFlags = {
    win32con.DISPLAY_DEVICE_ATTACHED_TO_DESKTOP: 'deskAttach',
    win32con.DISPLAY_DEVICE_MULTI_DRIVER: '(multiDrv)',
    win32con.DISPLAY_DEVICE_PRIMARY_DEVICE: 'primDev',
    win32con.DISPLAY_DEVICE_MIRRORING_DRIVER: 'mirrDrv',
    win32con.DISPLAY_DEVICE_VGA_COMPATIBLE: 'vgaCompat',
    win32con.DISPLAY_DEVICE_REMOVABLE: 'removable',
    win32con.DISPLAY_DEVICE_MODESPRUNED: 'modesPrun',
    win32con.DISPLAY_DEVICE_REMOTE: '(remote)',
    win32con.DISPLAY_DEVICE_DISCONNECT: '(disconn)'}


# flags returned when dev!=None
monitorFlags = {
    1: 'active', # DISPLAY_DEVICE_ACTIVE
    2: 'attached'} # DISPLAY_DEVICE_ATTACHED


# DEVMODE flags;
# note that wingdi.h says DM_GRAYSCALE and DM_INTERLACED are no longer valid
modeFlags = {
    win32con.DM_GRAYSCALE: 'grayscale',  # commented out from Win32 header
    win32con.DM_INTERLACED: 'interlaced',  # commented out from Win32 header
    4: 'textmode',  # DMDISPLAYFLAGS_TEXTMODE
    }
    

def flagsStr(flags, names):
    """Compose a string from some flags and a dict of names."""
    a = []
    for i in xrange(32):
        mask = 2**i
        if flags & mask and mask in names:
            a += [names[mask]]
            flags &= ~mask
    if flags:
        a += ['0x%08x' % flags]
    return ', '.join(a)


def getMode(dm):
    """Return the width, height, bpp and freq from a DEVMODE."""
    return (dm.PelsWidth, dm.PelsHeight, dm.BitsPerPel, dm.DisplayFrequency)


def buildMode(t):
    """Return a DEVMODE from a tuple of width, height, bpp and freq."""
    dm = pywintypes.DEVMODEType()
    dm.PelsWidth, dm.PelsHeight, dm.BitsPerPel, dm.DisplayFrequency = t
    dm.Fields = (win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT |
                 win32con.DM_BITSPERPEL | win32con.DM_DISPLAYFREQUENCY)
    return dm


def modeStr(t):
    """Return a string from a tuple of width, height, bpp and freq."""
    return '%d*%d %d-bit %dHz' % t


if __name__ == '__main__':
    print 'Adapters and devices:'
    for x in Devices():
        print '-'*70
        print '  name:', x.DeviceName
        print 'string:', x.DeviceString
        print ' state:', flagsStr(x.StateFlags, adapterFlags)
        print '    id:', x.DeviceID
        for y in Devices(x.DeviceName):
            print '\t', '-'*20
            print '\t', '  name:', y.DeviceName
            print '\t', 'string:', y.DeviceString
            print '\t', ' state:', flagsStr(y.StateFlags, monitorFlags)
            print '\t', '    id:', y.DeviceID
    print
    print 'Supported resolutions in default adapter'
    print '(! = unsupported by monitor):'
    monres = set(getMode(dm)[:2] for dm in Settings())
    rawres = set(getMode(dm)[:2] for dm in Settings(flags=EDS_RAWMODE))
    for xy in sorted(rawres):
        print '  %d*%d %s' % (xy[0], xy[1], ' ' if xy in monres else '!')
    print
    print 'Current mode:', modeStr(getMode(currentSettings()))
    print 'Registry mode:', modeStr(getMode(registrySettings()))
