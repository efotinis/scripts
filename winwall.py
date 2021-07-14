#!python3
"""Windows wallpaper functions."""

import argparse
import os

import win32api
import win32gui
from win32con import REG_SZ, SPI_GETDESKWALLPAPER, SPI_SETDESKWALLPAPER, SPIF_SENDCHANGE, SPIF_UPDATEINIFILE

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


def parse_args():
    ap = argparse.ArgumentParser(
        description='manage Windows wallpaper'
    )
    ap.add_argument(
        'path', 
        type=pathArg,
        nargs='?',
        help='image file; specify a dash ("-") to remove wallpaper; '
            'omit to print current path and style'
    )
    ap.add_argument(
        '-s', 
        dest='style', 
        choices=STYLE_VALUES, 
        default='fill',
        help='position style; default: %(default)s'
    )
    return ap.parse_args()


def pathArg(s):
    """Ensure image path is valid, absolute path or '-'."""
    if s != '-':
        s = os.path.abspath(s)
        if not os.path.isfile(s):
            raise argparse.ArgumentTypeError('image file not found')
    return s


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


if __name__ == '__main__':
    try:
        args = parse_args()
        if not args.path:
            path, style = get()
            print(path)
            print(style)
        elif args.path == '-':
            remove()
        else:
            set(args.path, args.style)
    except Exception as x:
        raise SystemExit(str(x))
