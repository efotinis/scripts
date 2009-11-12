"""Windows Clipboard utilities."""

from __future__ import print_function
import win32clipboard
from win32con import CF_UNICODETEXT, CF_TEXT, CF_LOCALE
import dllutil
from ctypes.wintypes import INT, LCID, LCTYPE, LPSTR


GetLocaleInfo = dllutil.winfunc(
    'kernel32', 'GetLocaleInfoA', INT, [LCID, LCTYPE, LPSTR, INT])


class Session:
    """Context manager for opening/closing the clipboard."""
    
    def __enter__(self, hwnd=0):
        win32clipboard.OpenClipboard(hwnd)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        win32clipboard.CloseClipboard()


def hasformat(fmt):
    """Test whether clipboard contains a specific format."""
    return win32clipboard.IsClipboardFormatAvailable(fmt)


def localecodepage(lcid):
    """Windows codepage number of a LCID.

    Returns None on error, or 0 for Unicode-only locales.
    """
    buf = ctypes.create_string_buffer(6)
    LOCALE_IDEFAULTANSICODEPAGE = 0x00001004
    res = GetLocaleInfo(lcid, LOCALE_IDEFAULTANSICODEPAGE, buf, len(buf))
    return int(buf.value) if res else None


def gettext():
    """Get clipboard text (always Unicode) or None."""
    with Session():
        ret = None
        # Windows provides automatic conversions between the following:
        #   on Win9x: CF_TEXT, CF_OEMTEXT
        #   on NT-based: CF_TEXT, CF_OEMTEXT, CF_UNICODETEXT
        if hasformat(CF_UNICODETEXT):
            ret = win32clipboard.GetClipboardData(CF_UNICODETEXT)
        elif hasformat(CF_TEXT):
            ret = win32clipboard.GetClipboardData(CF_TEXT)
            try:
                lcid = win32clipboard.GetClipboardData(CF_LOCALE)
                lcid = struct.unpack('L', lcid)[0]
                cp = localecodepage(lcid)
                if cp:
                    ret = ret.decode('cp' + str(cp))
            except TypeError:
                # CF_LOCALE not available
                pass
            if not isinstance(ret, unicode):
                ret = ret.decode('mbcs')
    return ret


def settext(s, lcid=None):
    """Set clipboard text, with optional locale if not Unicode.

    Unless set manually, Windows uses the current input language for the locale.
    """
    if isinstance(s, unicode) and lcid is not None:
        raise ValueError('locale not allowed for Unicode clipboard text')
    with Session():
        win32clipboard.EmptyClipboard()
        fmt = CF_UNICODETEXT if isinstance(s, unicode) else CF_TEXT
        win32clipboard.SetClipboardData(fmt, s)
        if lcid:
            win32clipboard.SetClipboardData(CF_LOCALE, struct.pack('L', lcid))


# predefined clipboard format names
standardformats = {
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
    15: 'CF_HDROP',
    16: 'CF_LOCALE',
    17: 'CF_DIBV5'}


def formatname(fmt):
    """Get format name (either custom or predefined)."""
    try:
        return standardformats[fmt]
    except KeyError:
        return win32clipboard.GetClipboardFormatName(fmt)


def enumformats():
    """List available clipboard formats."""
    with Session():
        ret, fmt = [], 0
        while True:
            fmt = win32clipboard.EnumClipboardFormats(fmt)
            if not fmt:
                break
            ret.append(fmt)
        return ret


if __name__ == '__main__':
    fmts = [formatname(n) for n in enumformats()]
    print('available clipboard formats:', ', '.join(fmts))
