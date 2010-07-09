import os
import ctypes

import win32con

import dllutil

from ctypes.wintypes import BOOL, DWORD, HANDLE, WCHAR, LPCWSTR, FILETIME
TCHAR = WCHAR
LPCTSTR = LPCWSTR

INVALID_HANDLE_VALUE = HANDLE(-1)

class Win32FindDataW(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('dwFileAttributes',   DWORD),
        ('ftCreationTime',     FILETIME),
        ('ftLastAccessTime',   FILETIME),
        ('ftLastWriteTime',    FILETIME),
        ('nFileSizeHigh',      DWORD),
        ('nFileSizeLow',       DWORD),
        ('dwReserved0',        DWORD),
        ('dwReserved1',        DWORD),
        ('cFileName',          TCHAR * win32con.MAX_PATH),
        ('cAlternateFileName', TCHAR * 14),
    ]
    def clone(self):
        ret = Win32FindDataW()
        for name, type in self._fields_:
            setattr(ret, name, getattr(self, name))
        return ret

krnl = dllutil.WinDLL('kernel32')
FindFirstFileW = krnl('FindFirstFileW', HANDLE, [LPCTSTR, ctypes.POINTER(Win32FindDataW)])
FindNextFileW = krnl('FindNextFileW', BOOL, [HANDLE, ctypes.POINTER(Win32FindDataW)])
FindClose = krnl('FindClose', BOOL, [HANDLE])

class FindFileW:
    '''Unicode WinAPI FindFirstFile (and family) wrapper.
    Caller *must* call close() to release resources,
    or just use it in a with statement.'''

    def __init__(self, mask):
        self.data = Win32FindDataW()
        self.handle = HANDLE(FindFirstFileW(mask, self.data))
        if not self.isOpen():
            self.data = None

##    def __del__(self):
##        # TODO: potentional leak; user must remember to call close()
##        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def isOpen(self):
        # NOTE: comparing 'value' (not the objects themselves)
        return self.handle.value != INVALID_HANDLE_VALUE.value

    def close(self):
        if self.isOpen():
            if not FindClose(self.handle):
                return False
            self.handle = INVALID_HANDLE_VALUE
        return True

    def findNext(self):
        ok = bool(FindNextFileW(self.handle, self.data))
        if not ok:
            self.data = None
        return ok

    def __iter__(self):
        return self
    
    def next(self):
        if not self.data:
            self.close()
            raise StopIteration
        ret = self.data.clone()
        self.findNext()
        return ret

# TODO: make named_tuple
class Info:
    def __init__(self, fd=None):
        if fd:
            self.attr = fd.dwFileAttributes
            self.create = fd.ftCreationTime.dwLowDateTime | (fd.ftCreationTime.dwHighDateTime << 32)
            self.access = fd.ftLastAccessTime.dwLowDateTime | (fd.ftLastAccessTime.dwHighDateTime << 32)
            self.modify = fd.ftLastWriteTime.dwLowDateTime | (fd.ftLastWriteTime.dwHighDateTime << 32)
            self.size = fd.nFileSizeLow | (fd.nFileSizeHigh << 32)
            self.res0 = fd.dwReserved0
            self.res1 = fd.dwReserved1
            self.name = fd.cFileName
            self.altName = fd.cAlternateFileName
        else:
            self.attr = 0
            self.create = 0
            self.access = 0
            self.modify = 0
            self.size = 0
            self.res0 = 0
            self.res1 = 0
            self.name = u''
            self.altName = u''
    def isDir(self):
        return self.attr & win32con.FILE_ATTRIBUTE_DIRECTORY

def getInfo(path):
    '''Get a single item's info or None.'''
    with FindFileW(path) as ff:
        for fd in ff:
            return Info(fd)
    return None

def dirList(dir, includeDummies=False):
    '''Get info list of a dir's items.'''
    ret = []
    dummies = ('.', '..')
    with FindFileW(os.path.join(dir, '*')) as ff:
        for fd in ff:
            if not includeDummies and fd.cFileName in dummies:
                continue
            ret.append(Info(fd))
    return ret

def walk(dir):
    """deprecated; use itemWalk()"""
    return itemWalk(dir)

def itemWalk(dirPath):
    """Recursively return parent path and item info."""
    subs = []
    for item in dirList(dirPath):
        yield dirPath, item
        if item.isDir():
            subs += [item.name]
    for s in subs:
        for ret in itemWalk(os.path.join(dirPath, s)):
            yield ret

def listWalk(dirPath):
    """Recursively return dir path and item info list."""
    items = dirList(dirPath)
    yield dirPath, items
    for sub in (x for x in items if x.isDir()):
        for ret in listWalk(os.path.join(dirPath, sub.name)):
            yield ret
