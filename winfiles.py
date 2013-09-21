"""Windows directory functions based on FindFirstFile/FindNextFile.

We can't use the win32file functions (FindFilesW, FindFilesIterator,
GetFileInformationByHandle, etc), because they return PyTime objects,
which (the last time I checked) are broken beyond all repair.
"""

##TODO:
##    walk()
##        - better follow os.walk, i.e. list dirs/files separately
##            (use case for unified listing?)
##    listdir()
##        - simply: list(find(os.path.join(path, '*'), dots, times))
##        - too simple to add? (use case?)

import ctypes
import collections
import datetime

import win32file
from ctypes.wintypes import (BOOL, LPCWSTR, HANDLE, WIN32_FIND_DATAW, DWORD,
    FILETIME)
from winerror import ERROR_NO_MORE_FILES
from win32con import FILE_ATTRIBUTE_DIRECTORY

import CommonTools


FindFirstFileW = ctypes.windll.kernel32.FindFirstFileW
FindFirstFileW.argtypes = [LPCWSTR, ctypes.POINTER(WIN32_FIND_DATAW)]
FindFirstFileW.restype = HANDLE

FindNextFileW = ctypes.windll.kernel32.FindNextFileW
FindNextFileW.argtypes = [HANDLE, ctypes.POINTER(WIN32_FIND_DATAW)]
FindNextFileW.restype = BOOL

FindClose = ctypes.windll.kernel32.FindClose
FindClose.argtypes = [HANDLE]
FindClose.restype = BOOL


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('dwFileAttributes', DWORD),
        ('ftCreationTime', FILETIME),
        ('ftLastAccessTime', FILETIME),
        ('ftLastWriteTime', FILETIME),
        ('dwVolumeSerialNumber', DWORD),
        ('nFileSizeHigh', DWORD),
        ('nFileSizeLow', DWORD),
        ('nNumberOfLinks', DWORD),
        ('nFileIndexHigh', DWORD),
        ('nFileIndexLow', DWORD),
    ]
    

GetFileInformationByHandle = ctypes.windll.kernel32.GetFileInformationByHandle
GetFileInformationByHandle.argtypes = [HANDLE,
    ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)]
GetFileInformationByHandle.restype = BOOL


INVALID_HANDLE_VALUE = -1
FILE_SHARE_ALL = (win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE |
                  win32file.FILE_SHARE_DELETE)


FindData = collections.namedtuple('FindData',
    'attr create access modify size res0 res1 name altname')

FileInfo = collections.namedtuple('FileInfo',
    'attr create access modify volume size links index')


def filetime_to_windows(ft):
    return ft.dwLowDateTime | (ft.dwHighDateTime << 32)

def filetime_to_unix(ft):
    return CommonTools.wintime_to_pyseconds(filetime_to_windows(ft))

def filetime_to_python(ft):
    return datetime.datetime.utcfromtimestamp(filetime_to_unix(ft))


TIME_CONV = {
    'windows': filetime_to_windows,
    'unix': filetime_to_unix,
    'python': filetime_to_python,
}


def find(path, dots=False, times='windows'):
    """Directory search; generates FindData objects.

    params:
    - path: string path; may include wildcards
    - dots: include special dot entries ('.' and '..)
    - times: type of times; one of:
        'windows'   int 100-nanoseconds since January 1, 1601
        'unix'      float seconds since Unix epoch (Jan 1, 1970)
        'python'    datetime object
    """
    times = TIME_CONV[times]
    data = WIN32_FIND_DATAW()
    h = FindFirstFileW(path, data)
    if h.value == -1:  # INVALID_HANDLE_VALUE
        x = ctypes.WinError()
        x.filename = path
        raise x
    try:
        while True:
            if dots or data.cFileName not in ('.', '..'):
                yield FindData(
                    attr=data.dwFileAttributes,
                    create=times(data.ftCreationTime),
                    access=times(data.ftLastAccessTime),
                    modify=times(data.ftLastWriteTime),
                    size=data.nFileSizeLow | (data.nFileSizeHigh << 32),
                    reserved0=data.dwReserved0,
                    reserved1=data.dwReserved1,
                    name=data.cFileName,
                    altname=data.cAlternateFileName)
            if not FindNextFileW(h, data):
                if ctypes.GetLastError() == ERROR_NO_MORE_FILES:
                    break
                raise ctypes.WinError()
    finally:
        FindClose(h)


def is_dir(n):
    """Test flags for directory attribute."""
    return bool(n & FILE_ATTRIBUTE_DIRECTORY)


def walk(path, times='windows', unified=False, onerror=None):
    """Directory tree generator.

    path: must be a directory; no wildcards allowed
    times: see find()
    onerror: see os.walk()
    unified: if true, generates (path,items); otherwise (path,dirs,files)

    TODO: remove 'unified' if it isn't really useful
    """
    # TODO: do we really need to check with isdir?
    if not os.path.isdir(path):
        raise ValueError('path is not a directory')
    for x in _walk(path, times=times, unified=unified, onerror=onerror):
        yield x


def _walk(path, times='windows', unified=False, onerror=None):
    """Implementation of walk()."""
    try:
        items = list(find(os.path.join(path, '*'), dots=False, times=times))
    except OSError as err:
        if onerror is not None:
            onerror(err)
    dirs = [item for item in items if is_dir(item.attr)]
    if unified:
        yield path, items
    else:
        files = [item for item in items if not is_dir(item.attr)]
        yield path, dirs, files
    for sub in dirs:
        for x in walk(os.path.join(path, sub.name), times, unified, onerror):
            yield x


def get_info(path, times='windows'):
    """Get file information (BY_HANDLE_FILE_INFORMATION)."""
    times = TIME_CONV[times]
    h = win32file.CreateFile(path, 0, FILE_SHARE_ALL, None,
                             win32file.OPEN_EXISTING, 0, 0)
    try:
        hfi = BY_HANDLE_FILE_INFORMATION()
        if not GetFileInformationByHandle(int(h), hfi):
            raise WinError()
        return FileInfo(
            attr=hfi.dwFileAttributes,
            create=times(hfi.ftCreationTime),
            access=times(hfi.ftLastAccessTime),
            modify=times(hfi.ftLastWriteTime),
            volume=hfi.dwVolumeSerialNumber,
            size=hfi.nFileSizeLow | (hfi.nFileSizeHigh << 32),
            links=hfi.nNumberOfLinks,
            index=hfi.nFileIndexLow | (hfi.nFileIndexHigh << 32))
    finally:
        h.Close()
