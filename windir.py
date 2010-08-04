"""Windows directory function.

This will replace the FindFileW module.
"""

#from __future__ import print_function

import ctypes
import time
import collections
import contextlib

import win32file

import dllutil

from ctypes.wintypes import BOOL, LPCWSTR, HANDLE, WIN32_FIND_DATAW
from winerror import ERROR_NO_MORE_FILES, ERROR_ACCESS_DENIED
from win32con import FILE_ATTRIBUTE_DIRECTORY


INVALID_HANDLE_VALUE = HANDLE(-1)

kernel32 = dllutil.WinDLL('kernel32')

FindFirstFileW = kernel32('FindFirstFileW', HANDLE, [LPCWSTR, ctypes.POINTER(WIN32_FIND_DATAW)])
FindNextFileW = kernel32('FindNextFileW', BOOL, [HANDLE, ctypes.POINTER(WIN32_FIND_DATAW)])
FindClose = kernel32('FindClose', BOOL, [HANDLE])

FindData = collections.namedtuple('FindData',
    'attrib create access modify size reserved0 reserved1 name altname')


@contextlib.contextmanager
def find_handle(path, data):
    """Directory search handle manager."""
    handle = FindFirstFileW(path, data)
    if handle == INVALID_HANDLE_VALUE.value:
        err = ctypes.WinError()
        err.filename = path
        raise err
    try:
        yield handle
    finally:
        FindClose(handle)


def find_files(path, dots=False, timefunc=None):
    """Directory search; generates FindData objects.

    Unless 'dots' is true, special dot entries ('.' and '..') are ignored.
    'timefunc' can be a function for transforming times (def. type is FILETIME).
    """
    data = WIN32_FIND_DATAW()
    with find_handle(path, data) as handle:
        while True:
            if dots or data.cFileName not in ('.', '..'):
                size = data.nFileSizeLow | (data.nFileSizeHigh << 32)
                create = data.ftCreationTime if timefunc is None else timefunc(data.ftCreationTime)
                access = data.ftLastAccessTime if timefunc is None else timefunc(data.ftLastAccessTime)
                modify = data.ftLastWriteTime if timefunc is None else timefunc(data.ftLastWriteTime)
                yield FindData(attrib=data.dwFileAttributes,
                               create=create, access=access, modify=modify, size=size,
                               reserved0=data.dwReserved0, reserved1=data.dwReserved1,
                               name=data.cFileName, altname=data.cAlternateFileName)
            if not FindNextFileW(handle, data):
                if ctypes.GetLastError() == ERROR_NO_MORE_FILES:
                    return
                raise ctypes.WinError()


def walk(path, timefunc=None, unified=False, onerror=None):
    """Directory tree generator.

    path: must be a directory; no wildcards allowed
    timefunc: see find_files()
    onerror: see os.walk()
    unified: if true, generates (path,items); otherwise (path,dirs,files)
    """
    if not os.path.isdir(path):
        raise ValueError('path is not a directory')
    for x in _walk(path, timefunc, unified, onerror):
        yield x


def _walk(path, timefunc=None, unified=False, onerror=None):
    """Implementation of walk()."""
    try:
        items = list(find_files(os.path.join(path, '*'), dots=False, timefunc=timefunc))
    except OSError as err:
        if onerror is not None:
            onerror(err)
    dirs = [item for item in items if item.attrib & FILE_ATTRIBUTE_DIRECTORY]
    if unified:
        yield path, items
    else:
        files = [item for item in items if not item.attrib & FILE_ATTRIBUTE_DIRECTORY]
        yield path, dirs, files
    for sub in dirs:
        for x in walk(os.path.join(path, sub.name), timefunc, unified, onerror):
            yield x


##import win32con
##import sys
##import os
##
##class Stats:
##    count = 0
##
##def test(path, stats):
##    try:
##        for x in find_files(os.path.join(path, '*')):
##            stats.count += 1
##            #print(x.name)
##            
##            if x.attrib & win32con.FILE_ATTRIBUTE_DIRECTORY:
##                test(os.path.join(path, x.name), stats)
##    except WindowsError as err:
##        if err.winerror == ERROR_ACCESS_DENIED:
##            print('access denied: "{0}"'.format(path), file=sys.stderr)
##        
##stats = Stats()
##test('c:/users/elias', stats)
##print('items: {0}'.format(stats.count))
