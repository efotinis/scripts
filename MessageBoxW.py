"""Unicode MessageBox support.

2007.12.02  created
"""

import ctypes


INT = ctypes.c_int
UINT = ctypes.c_uint
HWND = ctypes.c_void_p
LPCWSTR = ctypes.c_wchar_p
HGLOBAL = ctypes.c_void_p


MessageBoxW = ctypes.windll.user32.MessageBoxW
MessageBoxW.argtypes = [HWND, LPCWSTR, LPCWSTR, UINT]
MessageBoxW.restype = INT

if __name__ == '__main__':
    codes = (
        (0x00fa, 'latin'),
        (0x03b8, 'greek'),
        (0x0434, 'cyrillic'))
    s = '\n'.join('U+%04X: %s (%s)' % (n, unichr(n), s) for n, s in codes)
    MessageBoxW(0, s, u'unicode msg box', 0)
    