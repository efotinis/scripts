"""Monitor brightness/contrast control."""

import argparse
import ctypes
import itertools
from ctypes.wintypes import BOOL, HANDLE, DWORD, LPDWORD, WCHAR

import win32api

import dllutil


PHYSICAL_MONITOR_DESCRIPTION_SIZE = 128
class PHYSICAL_MONITOR(ctypes.Structure):
    _fields_ = [
        ('hPhysicalMonitor', HANDLE),
        ('szPhysicalMonitorDescription', WCHAR * PHYSICAL_MONITOR_DESCRIPTION_SIZE)
    ]
LPPHYSICAL_MONITOR = ctypes.POINTER(PHYSICAL_MONITOR)
dxva2 = dllutil.WinDLL('dxva2')
GetNumberOfPhysicalMonitorsFromHMONITOR = dxva2('GetNumberOfPhysicalMonitorsFromHMONITOR', BOOL, [HANDLE, LPDWORD])
GetPhysicalMonitorsFromHMONITOR = dxva2('GetPhysicalMonitorsFromHMONITOR', BOOL, [HANDLE, DWORD, LPPHYSICAL_MONITOR])
DestroyPhysicalMonitors = dxva2('DestroyPhysicalMonitors', BOOL, [DWORD, LPPHYSICAL_MONITOR])
GetMonitorBrightness = dxva2('GetMonitorBrightness', BOOL, [HANDLE, LPDWORD, LPDWORD, LPDWORD])
SetMonitorBrightness = dxva2('SetMonitorBrightness', BOOL, [HANDLE, DWORD])
GetMonitorContrast = dxva2('GetMonitorContrast', BOOL, [HANDLE, LPDWORD, LPDWORD, LPDWORD])
SetMonitorContrast = dxva2('SetMonitorContrast', BOOL, [HANDLE, DWORD])


def ValueOpt(s):
    rel = ''
    if s[:1] in '+-':
        rel = s[:1]
        s = s[1:]
    return rel, int(s)


def parse_args():
    ap = argparse.ArgumentParser(
        description='monitor brightness/contrast control',
        epilog='VAL can be 0..100; an optional +/- can be used')
    add = ap.add_argument
    add('-m', dest='monitors', type=int, default=0,
        help='monitor number (>0) or 0 (default) for all')
    add('-b', dest='brightness', metavar='VAL', type=ValueOpt,
        help='set brightness')
    add('-c', dest='contrast', metavar='VAL', type=ValueOpt,
        help='set contrast')
    args = ap.parse_args()
    if args.monitors < 0:
        args.monitors = 0
    return args


def cap(a, n, b):
    if n < a:
        return a
    if n > b:
        return b
    return n


class RangeValue:
    def __init__(self, minval, maxval):
        if minval >= maxval:
            raise ValueError('invalid value range: {}..{}'.format(minval, maxval))
        self.min = minval
        self.max = maxval
    def to_percent(self, value):
        return round(100 * (value - self.min) / (self.max - self.min))
    def from_percent(self, percent):
        percent = cap(0, percent, 100)
        return int(percent / 100 * (self.max - self.min) + self.min)


class PhysicalMonitor:
    def __init__(self, mon):
        self.mon = HANDLE(mon)
        self.brange = None
        self.crange = None

    @property
    def brightness(self):
        a, n, b = DWORD(), DWORD(), DWORD()
        if not GetMonitorBrightness(self.mon, a, n, b):
            raise RuntimeError('GetMonitorBrightness')
        self.brange = RangeValue(a.value, b.value)
        return self.brange.to_percent(n.value)

    @brightness.setter
    def brightness(self, value):
        if self.brange is None:
            dummy = self.brightness
        if not SetMonitorBrightness(self.mon, DWORD(self.brange.from_percent(value))):
            raise RuntimeError('SetMonitorBrightness')

    @property
    def contrast(self):
        a, n, b = DWORD(), DWORD(), DWORD()
        if not GetMonitorContrast(self.mon, a, n, b):
            raise RuntimeError('GetMonitorContrast')
        self.crange = RangeValue(a.value, b.value)
        return self.crange.to_percent(n.value)

    @contrast.setter
    def contrast(self, value):
        if self.crange is None:
            dummy = self.contrast
        if not SetMonitorContrast(self.mon, DWORD(self.crange.from_percent(value))):
            raise RuntimeError('SetMonitorContrast')


def change(pm, attr, rel, val):
    if rel == '':
        setattr(pm, attr, val)
    else:
        cur = getattr(pm, attr)
        if rel == '-':
            val = -val
        setattr(pm, attr, cur + val)


def main(args):
##    for i in itertools.count():
##        try:
##            dd = win32api.EnumDisplayDevices(None, i, 0)
##        except win32api.error:
##            break
##        print(i, dd.DeviceName, dd.DeviceString)  # dd.StateFlags

    index = 1
    for mon, dc, rect, in win32api.EnumDisplayMonitors():
##        h = mon.handle & 0xffffffff
##        print('0x{:08x} {}'.format(h, rect))
##        print(win32api.GetMonitorInfo(mon))

        n = DWORD()
        if not GetNumberOfPhysicalMonitorsFromHMONITOR(mon.handle, n):
            raise RuntimeError('GetNumberOfPhysicalMonitorsFromHMONITOR')
        a = (PHYSICAL_MONITOR * n.value)()
        if not GetPhysicalMonitorsFromHMONITOR(mon.handle, n, a):
            raise RuntimeError('GetPhysicalMonitorsFromHMONITOR')
        for i in range(n.value):
            if args.monitors == 0 or args.monitors == index:
                pm = PhysicalMonitor(a[i].hPhysicalMonitor)
                if args.brightness:
                    change(pm, 'brightness', *args.brightness)
                if args.contrast:
                    change(pm, 'contrast', *args.contrast)
                print('#{}  B:{:<4} C:{:<4}  {}'.format(
                    index,
                    str(pm.brightness) + '%',
                    str(pm.contrast) + '%',
                    a[i].szPhysicalMonitorDescription))
            index += 1
        DestroyPhysicalMonitors(n, a)


if __name__ == '__main__':
    main(parse_args())
