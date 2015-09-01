#!python3
"""Windows wallpaper functions."""

import winreg

import reg_util
import win32api
import win32con
import win32gui


REG_ROOT = winreg.HKEY_CURRENT_USER
REG_PATH = 'Control Panel\\Desktop'
STYLE_VALUES = {  # WallpaperStyle/TileWallpaper values
    'tile': ('0', '1'),
    'center': ('0', '0'),
    'stretch': ('2', '0'),
    'fit': ('6', '0'),
    'fill': ('10', '0'),
}
WIN7_ONLY_STYLES = ('fit', 'fill')
IS_WIN7_OR_NEWER = win32api.GetVersionEx()[:2] >= (6, 1)


def _getval(key, name, typ):
    """Get a Registry value of a specific type."""
    val, typ = winreg.QueryValueEx(key, name)
    if typ != typ:
        raise TypeError('unexpected value type')
    return val


def get():
    """Get path and style of wallpaper."""
    with reg_util.open_key(REG_ROOT, REG_PATH) as k:
        s = _getval(k, 'WallpaperStyle', winreg.REG_SZ)
        if s == '0':
            s = _getval(k, 'TileWallpaper', winreg.REG_SZ)
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
    return win32gui.SystemParametersInfo(win32con.SPI_GETDESKWALLPAPER), style


def set(path=None, style=None):
    """Set path and style of wallpaper.

    Arguments set to None are not changed.
    Setting path to '' removes the wallpaper.
    """
    if style is not None:
        if style in WIN7_ONLY_STYLES and not IS_WIN7_OR_NEWER:
            raise ValueError('fit/fill styles require Windows 7 or later')
        style, tile = STYLE_VALUES[style]
        with reg_util.create_key(REG_ROOT, REG_PATH) as k:
            winreg.SetValueEx(k, 'WallpaperStyle', 0, winreg.REG_SZ, style)
            winreg.SetValueEx(k, 'TileWallpaper', 0, winreg.REG_SZ, tile)
    win32gui.SystemParametersInfo(
        win32con.SPI_SETDESKWALLPAPER,
        path,
        win32con.SPIF_SENDCHANGE | win32con.SPIF_UPDATEINIFILE)


def remove():
    """Remove wallpaper."""
    set('')
