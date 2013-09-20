"""Windows command line functions."""

import sys
if sys.platform != 'win32':
    raise Exception('unsupported platform: ' + sys.platform)

import ctypes
from ctypes.wintypes import INT, LPWSTR, LPCWSTR, HLOCAL


PINT = ctypes.POINTER(INT)

GetCommandLineW = ctypes.windll.kernel32.GetCommandLineW
GetCommandLineW.argtypes = []
GetCommandLineW.restype = LPWSTR

CommandLineToArgvW = ctypes.windll.shell32.CommandLineToArgvW
CommandLineToArgvW.argtypes = [LPCWSTR, PINT]
CommandLineToArgvW.restype = ctypes.POINTER(LPWSTR)

LocalFree = ctypes.windll.kernel32.GlobalFree
LocalFree.argtypes = [HLOCAL]
LocalFree.restype = HLOCAL


def get_original():
    """Original, raw command line (unicode)."""
    return GetCommandLineW()


def split(s):
    """Split a cmdline string according to platform rules."""
    count = INT()
    a = CommandLineToArgvW(s, count)
    if not a:
        raise ctypes.WinError()
    try:
        return [a[i] for i in range(count.value)]
    finally:
        if a:
            LocalFree(a)


def get_argv():
    """Get a list of unicode string by splitting the original cmdline."""
    return split(get_original())


