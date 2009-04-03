# 2007.04.17  Created.
# 2007.09.27  Modified.
# 2008.01.27  Used SharedLib.
# 2008.07.23  Fixed subtle bug where DWORD was defined as ctypes.c_int,
#             instead of ctypes.c_ulong. I was perplexed by the fact that
#             50% of the time, dates returned from this module where ~419
#             seconds off. I noticed that 419 = 2^32 / 10^7, 2^32 being
#             the max DWORD and 10^7 the scale of Windows file times
#             (100s of nanoseconds). That's when I knew it was a sign error.
#             I lulz'ed a little... :)

from __future__ import with_statement
import os
import ctypes
import win32con
import SharedLib

HANDLE = ctypes.c_void_p
LPWCHAR = ctypes.c_wchar_p
DWORD = ctypes.c_ulong
BOOL = ctypes.c_int
TCHAR = ctypes.c_wchar
FILETIME = DWORD * 2

INVALID_HANDLE_VALUE = HANDLE(-1)

class Win32FindDataW(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('dwFileAttributes', DWORD),
        ('ftCreationTime',   FILETIME),
        ('ftLastAccessTime', FILETIME),
        ('ftLastWriteTime',  FILETIME),
        ('nFileSizeHigh',    DWORD),
        ('nFileSizeLow',     DWORD),
        ('dwReserved0',      DWORD),
        ('dwReserved1',      DWORD),
        ('cFileName',          TCHAR * win32con.MAX_PATH),
        ('cAlternateFileName', TCHAR * 14),
    ]
    def clone(self):
        ret = Win32FindDataW()
        for name, type in self._fields_:
            setattr(ret, name, getattr(self, name))
        return ret

krnl = SharedLib.WinLib('kernel32')
FindFirstFileW = krnl('FindFirstFileW', HANDLE, [LPWCHAR, ctypes.POINTER(Win32FindDataW)])
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

def int64(n1, n2):
    return n1 + (n2 << 32)

class Info:
    def __init__(self, fd=None):
        if fd:
            self.attr = fd.dwFileAttributes
            self.create = int64(fd.ftCreationTime[0], fd.ftCreationTime[1])
            self.access = int64(fd.ftLastAccessTime[0], fd.ftLastAccessTime[1])
            self.modify = int64(fd.ftLastWriteTime[0], fd.ftLastWriteTime[1])
            self.size = int64(fd.nFileSizeLow, fd.nFileSizeHigh)
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
