"""Unicode MessageBox support."""

import ctypes
from ctypes.wintypes import INT, UINT, HWND, LPCWSTR, HGLOBAL


MessageBoxW = ctypes.windll.user32.MessageBoxW
MessageBoxW.argtypes = [HWND, LPCWSTR, LPCWSTR, UINT]
MessageBoxW.restype = INT

if __name__ == '__main__':
    import six
    codes = (
        (0x00fa, 'latin'),
        (0x03b8, 'greek'),
        (0x0434, 'cyrillic'))
    s = '\n'.join('U+%04X: %s (%s)' % (n, six.unichr(n), s) for n, s in codes)
    MessageBoxW(0, s, u'unicode msg box', 0)
