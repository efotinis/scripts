# new (more Pythonic) module, based on Display.py

from __future__ import print_function

import win32api
import win32con
import pywintypes


# EnumDisplaySettingsEx flag
EDS_RAWMODE = 2

# DISP_CHANGE_xxx number to string
SET_MODE_RET_STR = dict((getattr(win32con, s), s)
    for s in dir(win32con) if s.startswith('DISP_CHANGE_'))


def adapters():
    """Iterator of display adapters (PyDISPLAY_DEVICE)."""
    return _Devices()


def monitors(adapter):
    """Iterator of adapter monitors (PyDISPLAY_DEVICE)."""
    return _Devices(adapter)


def modes(adapter=None, raw=False):
    """Iterator of graphics modes (PyDEVMODE)."""
    return _Settings(adapter, EDS_RAWMODE if raw else 0)


def getMode(adapter=None, registry=False):
    """Currently effective mode (PyMODE) or the mode stored in registry."""
    return win32api.EnumDisplaySettings(adapter,
        win32con.ENUM_REGISTRY_SETTINGS if registry else
        win32con.ENUM_CURRENT_SETTINGS)
    

def setMode(adapter=None, mode=None, flags=0):
    """Change mode using a PyDEVMODE or (width,height,bpp,freq)."""
    if mode is not None and not isinstance(mode, pywintypes.DEVMODEType):
        mode = makeDevMode(mode)
    return win32api.ChangeDisplaySettingsEx(adapter, mode, flags)


def resetMode(adapter=None):
    """Reset to registry stored mode."""
    return setMode(adapter, None)


class _Enumerator(object):
    
    def __init__(self):
        """Base enumerator class for EnumDisplayXxx API."""
        self.index = 0

    def enum(self, i):
        """Derived classes must return an item.

        A win32api exception will stop the enumeration.
        """
        raise NotImplementedError

    def __iter__(self):
        return self

    def __next__(self):
        try:
            ret = self.enum(self.index)
            self.index += 1
            return ret
        except win32api.error:
            raise StopIteration

    def next(self):
        return self.__next__()


class _Devices(_Enumerator):

    def __init__(self, dev=None):
        """Iterator for adapters (dev==None) or monitors (dev!=None)."""
        _Enumerator.__init__(self)
        self.dev = dev

    def enum(self, i):
        return win32api.EnumDisplayDevices(self.dev, i)


class _Settings(_Enumerator):    

    def __init__(self, dev=None, flags=0):
        """Modes iterator."""
        _Enumerator.__init__(self)
        self.dev = dev
        self.flags = flags

    def enum(self, i):
        return win32api.EnumDisplaySettingsEx(self.dev, i, self.flags)


def getDevMode(dm):
    """Get (width,height,bpp,freq) from a PyDEVMODE."""
    return (dm.PelsWidth, dm.PelsHeight, dm.BitsPerPel, dm.DisplayFrequency)


def makeDevMode(t):
    """Convert (width,height,bpp,freq) to a PyDEVMODE."""
    dm = pywintypes.DEVMODEType(0)  # DriverExtra=0
    dm.PelsWidth, dm.PelsHeight, dm.BitsPerPel, dm.DisplayFrequency = t
    dm.Fields = (win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT |
                 win32con.DM_BITSPERPEL | win32con.DM_DISPLAYFREQUENCY)
    return dm


def modeStr(m):
    """Format a (width,height,bpp,freq) tuple or PyDEVMODE for display."""
    fmt = '{0}x{1} {2}-bit {3}Hz'
    try:
        return fmt.format(*getDevMode(m))
    except AttributeError:
        return fmt.format(*m)


if __name__ == '__main__':

    def getModeStrSafely(adapter=None, registry=False):
        try:
            return modeStr(getMode(adapter, registry))
        except win32api.error:
            return None

    print()
    print('Display adapters:')
    for adp in adapters():
        print()
        print('{0} [{1}]'.format(adp.DeviceString, adp.DeviceName))
        supModes = tuple(modes(adp.DeviceName))
        rawModes = tuple(modes(adp.DeviceName, raw=True))
        supResls = tuple(sorted(set(getDevMode(m)[:2] for m in supModes)))
        rawResls = tuple(sorted(set(getDevMode(m)[:2] for m in rawModes)))
        print('  monitors:', ', '.join(mon.DeviceString for mon in monitors(adp.DeviceName)))
        print('  current mode:', getModeStrSafely(adp.DeviceName))
        print('  registry mode:', getModeStrSafely(adp.DeviceName, registry=True))
        print('  modes (supported/raw):', len(supModes), len(rawModes))
        print('  resolutions:', ', '.join(
            ('{0}x{1}' if wh in supResls else '({0}x{1})').format(*wh)
            for wh in rawResls))
