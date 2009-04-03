"""Unicode command line support.

2007.12.02  created
"""

import ctypes


LPWSTR = LPCWSTR = ctypes.c_wchar_p
PINT = ctypes.POINTER(ctypes.c_int)
HGLOBAL = ctypes.c_void_p


GetCommandLineW = ctypes.windll.kernel32.GetCommandLineW
GetCommandLineW.argtypes = []
GetCommandLineW.restype = LPWSTR

CommandLineToArgvW = ctypes.windll.shell32.CommandLineToArgvW
CommandLineToArgvW.argtypes = [LPCWSTR, PINT]
CommandLineToArgvW.restype = ctypes.POINTER(LPWSTR)

# NOTE: GlobalFree barfs on NULL; must check for it
GlobalFree = ctypes.windll.kernel32.GlobalFree
GlobalFree.argtypes = [HGLOBAL]
GlobalFree.restype = HGLOBAL


def getargvw():
    """Return the argv list with Unicode strings."""
    s = GetCommandLineW()
    count = ctypes.c_int()
    array = CommandLineToArgvW(s, ctypes.byref(count))
    if array:
        a = [array[i] for i in range(count.value)]
        GlobalFree(array)
    else:
        a = []
    a = a[1:]  # strip Python EXE, just like sys.argv
    if not a:
        a = [u'']  # use empty string if there's no script, just like sys.argv
    return a


if __name__ == '__main__':
    import sys
    print 'sys.argv:'
    for i, s in enumerate(sys.argv):
        print '  #%d: %s' % (i, s)
    print 'getargvw():'
    for i, s in enumerate(getargvw()):
        print '  #%d: %s' % (i, s)
        