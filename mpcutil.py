"""MPC-HC utilities."""

from __future__ import print_function, division
import collections
import itertools
import os
import re

import winregx

try:
    from _winreg import HKEY_CURRENT_USER, REG_SZ, REG_DWORD, KEY_WRITE
except ImportError:
    from winreg import HKEY_CURRENT_USER, REG_SZ, REG_DWORD, KEY_WRITE


#ROOT = 'Software\\Gabest\\Media Player Classic\\'  # used before ~v1.7.2
ROOT = 'Software\\MPC-HC\\MPC-HC\\'

REG_FAVORITES = ROOT + 'Favorites\\Files'
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




#------------------------------
def get_value_data(key, name, type_, default=None):
    """Get value data; use default if missing or of different type."""
    try:
        data, valtype = key.getvalue(name)
        return data if valtype == type_ else default
    except WindowsError as x:
        if x.winerror == ERROR_FILE_NOT_FOUND:
            return default
        raise


# TODO: replace 'end' with 'count' in get/set_list()


def get_list(key, basename, type_=REG_SZ, start=0, end=None):
    """Get list of (index,data) of consecutive 'basenameN' values.

    Values not of type_ are ignored. If end is None, the first missing
    value stops enumeration, otherwise missing values are ignored. The
    ending index is not included.
    """
    if end is not None and end <= start:
        raise ValueError('end must be >start or None')
    ret = []
    for i in itertools.count(start):
        if end is not None and i >= end:
            break
        name = basename + str(i)
        data, curtype = key.getvalue(name)
        if data is None:
            if end is None:
                break
            else:
                continue
        if curtype != type_:
            continue
        ret.append((i, data))
    return ret


def set_list(key, basename, type_, data, start=0, end=None):
    """Set homogeneous list (data) of consecutive 'basenameN' values.

    If end is None, the value after the last one is deleted, otherwise
    all values up to (but not including) the ending index are deleted.

    Returns True if everything succeeded.
    """
    if end is not None and end <= start:
        raise ValueError('end must be >start or None')
    if end is not None and end - start > len(data):
        raise ValueError('too many items specified')

    error = False

    i = start
    for x in data:
        name = basename + str(i)
        if key.setvalue(name, (x, type_)):
            i += 1
        else:
            error = True

    if end is None:
        # unbound list; clear one
        name = basename + str(i)
        if not delete_value(key, name):
            error = True
    else:
        # bound list; clear all
        while i < end:
            name = basename + str(i)
            if not delete_value(key, name):
                error = True
            i += 1

    return not error
#------------------------------




def get_exe_path():
    """MPC-HC executable path, as stored in the Registry, or None."""
    with winregx.open(HKEY_CURRENT_USER, ROOT) as key:
        return get_value_data(key, 'ExePath', REG_SZ)


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
    with winregx.open(HKEY_CURRENT_USER, REG_FAVORITES) as key:
        for i, data in get_list(key, 'Name', REG_SZ, start=0):
            ret.append(fav_from_str(data))
    return ret


def set_favorites(favs):
    """Set Favorite objects to the Registry and return total success."""
    data = [fav_to_str(fav) for fav in favs]
    with winregx.create(HKEY_CURRENT_USER, REG_FAVORITES) as key:
        return set_list(key, 'Name', REG_SZ, data, start=0)


def get_saved_positions():
    """Get dict mapping file paths to saved positions."""
    filecount = get_recent_files_count()
    paths, positions = {}, {}
    with winregx.open(HKEY_CURRENT_USER, REG_SETTINGS) as key:
        for i, data in get_list(key, 'File Name ', REG_SZ, start=0, end=filecount):
            paths[i] = data
        for i, data in get_list(key, 'File Position ', REG_SZ, start=0, end=filecount):
            positions[i] = int(data) / TIMERES
    return {paths[i]:positions[i] for i in paths if i in positions}


def get_recent_files():
    """Get Recent objects from the Registry."""
    filecount = get_recent_files_count()
    positions = {os.path.normcase(path):pos for path, pos in
                 get_saved_positions().items()}
    ret = []
    with winregx.open(HKEY_CURRENT_USER, REG_RECENT) as key:
        for i, data in get_list(key, 'File', REG_SZ, start=1, end=filecount + 1):
            ret.append(Recent(
                path=data,
                position=positions.get(os.path.normcase(data), 0.0)
            ))
    return ret


def get_recent_files_count():
    """Number of recent files options."""
    with winregx.open(HKEY_CURRENT_USER, REG_SETTINGS) as key:
        return get_value_data(key, 'RecentFilesNumber', REG_DWORD, DEF_RECENTCOUNT)


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
