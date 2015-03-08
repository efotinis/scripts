"""Disk management utilities."""

import win32file
import win32con


def logical_drives(typefilter=None):
    """String of available disk drives letters (e.g. 'ACD').

    Result can be filtered by drive type (a single win32con.DRIVE_* value
    or a sequence of them).
    """
    bm = win32file.GetLogicalDrives()
    letters = ''.join(chr(ord('A') + i) for i in range(26) if bm & (2 ** i))
    if typefilter is not None:
        try:
            typefilter = set(typefilter)
        except TypeError:
            typefilter = set([typefilter])
        letters = ''.join(c for c in letters
                          if win32file.GetDriveType(c + ':\\') in typefilter)
    return letters
