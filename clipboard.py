# 2007.04.18: created; simple get/setText (CF_TEXT only)
# 2007.11.27: also handle CF_UNICODETEXT;
#             added stdFmtNames and enumAllFormats

# 2008.10.19: added Session,hasformat; refactored code using them
#             renamed items according to PEP8 (e.g. stdFmtNames to standardformats)
#
"""Windows Clipboard utilities."""


import win32clipboard
import win32con


class Session:
    """Context manager for opening/closing the clipboard."""
    
    def __enter__(self, hwnd=0):
        win32clipboard.OpenClipboard(hwnd)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        win32clipboard.CloseClipboard()


def hasformat(fmt):
    """Test whether clipboard contains a specific format."""
    return win32clipboard.IsClipboardFormatAvailable(fmt)


def gettext():
    """Get clipboard text (may be unicode), or '' if no text is available."""
    with Session():
        s = ''
        # NT-based system synthesize CF_UNICODETEXT when only CF_TEXT is available.
        # So, this function will always return a unicode string.
        # We could use EnumClipboardFormats to make sure we don't get the synth'ed
        # format, but that's probably not worth it.
        if hasformat(win32con.CF_UNICODETEXT):
            s = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        elif hasformat(win32con.CF_TEXT):
            s = win32clipboard.GetClipboardData(win32con.CF_TEXT)
        return s


def settext(s):
    """Set clipboard text (may be unicode)."""
    with Session():
        win32clipboard.EmptyClipboard()
        fmt = win32con.CF_UNICODETEXT if isinstance(s, unicode) else win32con.CF_TEXT
        win32clipboard.SetClipboardData(fmt, s)


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
    print 'avaiable clipboard formats:', ', '.join(fmts)
    
    