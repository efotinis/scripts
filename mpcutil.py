"""MPC-HC utilities."""

from __future__ import print_function, division
import collections
import os
import re

import reg_util

try:
    from _winreg import HKEY_CURRENT_USER, REG_SZ, REG_DWORD, KEY_WRITE
except ImportError:
    from winreg import HKEY_CURRENT_USER, REG_SZ, REG_DWORD, KEY_WRITE


#ROOT = 'Software\\Gabest\\Media Player Classic\\'  # used before ~v1.7.2
ROOT = 'Software\MPC-HC\MPC-HC\\'

REG_FAVORITES = ROOT + 'Favorites\Files'
REG_SETTINGS = ROOT + 'Settings'
REG_RECENT = ROOT + 'Recent File List'

DEF_RECENTCOUNT = 20
TIMERES = 10000000  # resolution of time positions


# fields:
#   name (text): menu item name
#   position (float): position in seconds
#   reldrive (bool): relative drive search enabled
#   path (text): file path
Favorite = collections.namedtuple('Favorite', 'name position reldrive path')


# fields:
#   path (text): file path
#   position (float): saved position in seconds (resolution is 1s/10,000,000)
Recent = collections.namedtuple('Recent', 'path position')


def get_exe_path():
    """MPC-HC executable path, as stored in the Registry, or None."""
    with reg_util.open_key(HKEY_CURRENT_USER, ROOT) as key:
        return reg_util.get_value_data(key, 'ExePath', REG_SZ)


def fav_from_str(s):
    """Convert Registry string value to Favorite."""
    # NOTE: only ';' is escaped to '\;'; nothing else (not even '\')
    a = re.split(r'(?<!\\);', s)  # split on non-escaped semicolons
    return Favorite(
        name=a[0].replace('\;', ';'),
        position=int(a[1]) / TIMERES,
        reldrive=bool(int(a[2])),
        path=a[3].replace('\;', ';')
    )


def fav_to_str(fav):
    """Convert Favorite to Registry string value."""
    return ';'.join([
        fav.name.replace(';', '\;'),
        str(int(round(fav.position * TIMERES))),
        '1' if fav.reldrive else '0',
        fav.path.replace(';', '\;')
    ])


def get_favorites():
    """Get Favorite objects from the Registry."""
    ret = []
    with reg_util.open_key(HKEY_CURRENT_USER, REG_FAVORITES) as key:
        for i, data in reg_util.get_list(key, 'Name', REG_SZ, start=0):
            ret.append(fav_from_str(data))
    return ret


def set_favorites(favs):
    """Set Favorite objects to the Registry and return total success."""
    data = [fav_to_str(fav) for fav in favs]
    with reg_util.create_key(HKEY_CURRENT_USER, REG_FAVORITES) as key:
        return reg_util.set_list(key, 'Name', REG_SZ, data, start=0)


def get_saved_positions():
    """Get dict mapping file paths to saved positions."""
    filecount = get_recent_files_count()
    paths, positions = {}, {}
    with reg_util.open_key(HKEY_CURRENT_USER, REG_SETTINGS) as key:
        for i, data in reg_util.get_list(key, 'File Name ', REG_SZ,
                                        start=0, end=filecount):
            paths[i] = data
        for i, data in reg_util.get_list(key, 'File Position ', REG_SZ,
                                        start=0, end=filecount):
            positions[i] = int(data) / TIMERES
    return {paths[i]:positions[i] for i in paths if i in positions}


def get_recent_files():
    """Get Recent objects from the Registry."""
    filecount = get_recent_files_count()
    positions = {os.path.normcase(path):pos for path, pos in
                 get_saved_positions().items()}
    ret = []
    with reg_util.open_key(HKEY_CURRENT_USER, REG_RECENT) as key:
        for i, data in reg_util.get_list(key, 'File', REG_SZ,
                                        start=1, end=filecount + 1):
            ret.append(Recent(
                path=data,
                position=positions.get(os.path.normcase(data), 0.0)
            ))
    return ret


def get_recent_files_count():
    """Number of recent files options."""
    with reg_util.open_key(HKEY_CURRENT_USER, REG_SETTINGS) as key:
        return reg_util.get_value_data(key, 'RecentFilesNumber',
                                      REG_DWORD, DEF_RECENTCOUNT)


if __name__ == '__main__':
    from timer import pretty_time
    print('favorites:')
    for fav in get_favorites():
        timepos = pretty_time(fav.position)
        s = '  {} "{}"'.format(timepos, fav.path)
        if fav.name != os.path.basename(fav.path):
            s += ' ({})'.format(fav.name)
        print(s)
    print('recent:')
    for rec in get_recent_files():
        timepos = pretty_time(rec.position)
        s = '  {} "{}"'.format(timepos, rec.path)
        print(s)
