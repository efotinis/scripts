#!python3
"""Windows wallpaper functions."""

import win32api
from win32con import REG_SZ, SPI_GETDESKWALLPAPER, SPI_SETDESKWALLPAPER, SPIF_SENDCHANGE, SPIF_UPDATEINIFILE
import win32gui

import winregx


REGPATH = r'HKCU\Control Panel\Desktop'
STYLE_VALUES = {  # WallpaperStyle/TileWallpaper values
    'tile': ('0', '1'),
    'center': ('0', '0'),
    'stretch': ('2', '0'),
    'fit': ('6', '0'),
    'fill': ('10', '0'),
}
WIN7_ONLY_STYLES = ('fit', 'fill')
IS_WIN7_OR_NEWER = win32api.GetVersionEx()[:2] >= (6, 1)


def _getval(key, name, reqtype):
    """Get a Registry value of a specific type."""
    val, type_ = key.getvalue(name)
    if type_ != reqtype:
        raise TypeError('unexpected value type')
    return val


def get():
    """Get path and style of wallpaper."""
    with winregx.open(None, REGPATH) as k:
        s = _getval(k, 'WallpaperStyle', REG_SZ)
        if s == '0':
            s = _getval(k, 'TileWallpaper', REG_SZ)
            style = 'tile' if s == '1' else 'center'
        elif s == '2':
            style = 'stretch'
        elif s == '6':
            style = 'fit'
        elif s == '10':
            style = 'fill'
        else:
            msg = 'unexpected WallpaperStyle value data: {}'.format(s)
            raise ValueError(msg)
    return win32gui.SystemParametersInfo(SPI_GETDESKWALLPAPER), style


def set(path=None, style=None):
    """Set path and style of wallpaper.

    Arguments set to None are not changed.
    Setting path to '' removes the wallpaper.
    """
    if style is not None:
        if style in WIN7_ONLY_STYLES and not IS_WIN7_OR_NEWER:
            raise ValueError('fit/fill styles require Windows 7 or later')
        style, tile = STYLE_VALUES[style]
        with winregx.create(None, REGPATH) as k:
            k.setvalue('WallpaperStyle', (style, REG_SZ))
            k.setvalue('TileWallpaper', (tile, REG_SZ))
    win32gui.SystemParametersInfo(
        SPI_SETDESKWALLPAPER, path, SPIF_SENDCHANGE | SPIF_UPDATEINIFILE)


def remove():
    """Remove wallpaper."""
    set('')
