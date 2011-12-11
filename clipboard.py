"""Windows Clipboard utilities."""

from __future__ import print_function
import struct
import win32clipboard
import win32con
import six
from ctypes.wintypes import INT, LCID, LCTYPE, LPSTR


class Session:
    """Context manager for opening/closing the clipboard."""
    
    def __enter__(self, hwnd=0):
        win32clipboard.OpenClipboard(hwnd)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        win32clipboard.CloseClipboard()


def has_format(fmt):
    """Test whether clipboard contains a specific format."""
    return win32clipboard.IsClipboardFormatAvailable(fmt)


def get_text():
    """Get Unicode text."""
    with Session():
        if not has_format(win32clipboard.CF_UNICODETEXT):
            raise TypeError('no CF_UNICODETEXT in clipboard')
        return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)

def set_text(text):
    """Set Unicode text."""
    if not isinstance(text, six.text_type):
        raise TypeError('text must be unicode')
    with Session():
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)

def get_text_with_locale():
    """Get non-Unicode text and locale."""
    with Session():
        if not has_format(win32clipboard.CF_TEXT):
            raise TypeError('no CF_TEXT in clipboard')
        text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
        # NOTE: if CF_TEXT is present, so is CF_LOCALE
        lcid_data = win32clipboard.GetClipboardData(win32clipboard.CF_LOCALE)
        (lcid,) = struct.unpack('L', lcid_data)
        return text, lcid
        
def set_text_with_locale(text, lcid):
    """Set non-Unicode text and locale."""
    if not isinstance(text, six.binary_type):
        raise TypeError('text must be binary')
    with Session():
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_TEXT, text)
        lcid_data = struct.pack('L', lcid)
        wrapper = memoryview if six.PY3 else buffer  # prevents pywin32 from appending a NUL
        win32clipboard.SetClipboardData(win32clipboard.CF_LOCALE, wrapper(lcid_data))


# names of predefined clipboard formats
STD_FMT_NAMES = {
    1: 'CF_TEXT',
    2: 'CF_BITMAP',
    3: 'CF_METAFILEPICT',
    4: 'CF_SYLK',
    5: 'CF_DIF',
    6: 'CF_TIFF',
    7: 'CF_OEMTEXT',
    8: 'CF_DIB',
    9: 'CF_PALETTE',
    10: 'CF_PENDATA',
    11: 'CF_RIFF',
    12: 'CF_WAVE',
    13: 'CF_UNICODETEXT',
    14: 'CF_ENHMETAFILE',
    15: 'CF_HDROP',   # WINVER >= 0x0400
    16: 'CF_LOCALE',  # WINVER >= 0x0400
    17: 'CF_DIBV5',   # WINVER >= 0x0500
    0x0080: 'CF_OWNERDISPLAY',
    0x0081: 'CF_DSPTEXT',
    0x0082: 'CF_DSPBITMAP',
    0x0083: 'CF_DSPMETAFILEPICT',
    0x008E: 'CF_DSPENHMETAFILE',
    }


def get_format_name(fmt):
    """Get format name (either custom or predefined)."""
    try:
        return STD_FMT_NAMES[fmt]
    except KeyError:
        pass

    if win32con.CF_PRIVATEFIRST <= fmt <= win32con.CF_PRIVATELAST:
        return 'CF_PRIVATEFIRST' + str(fmt - win32con.CF_PRIVATEFIRST)

    if win32con.CF_GDIOBJFIRST <= fmt <= win32con.CF_GDIOBJLAST:
        return 'CF_GDIOBJFIRST' + str(fmt - win32con.CF_GDIOBJFIRST)

    return win32clipboard.GetClipboardFormatName(fmt)


def enum_formats():
    """Generator of available formats."""
    with Session():
        current = 0
        while True:
            current = win32clipboard.EnumClipboardFormats(current)
            if not current:
                break
            yield current


def cb(s=None):
    """Get/set clipboard text.

    Interactive interpreter utility added via PYTHONSTARTUP.
    """
    if s is None:
        return get_text()
    else:
        set_text(s)


if __name__ == '__main__':
    names = [get_format_name(n) for n in enum_formats()]
    print('available clipboard formats:', ', '.join(names))
