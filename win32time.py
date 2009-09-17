"""WinAPI time wrappers."""

import time
import ctypes
import SharedLib
from ctypes.wintypes import BOOL, WORD, DWORD, LONG, WCHAR

LPWORD = ctypes.POINTER(WORD)
ULONGLONG = ctypes.c_uint64


class SYSTEMTIME(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('wYear', WORD),
        ('wMonth', WORD),
        ('wDayOfWeek', WORD),
        ('wDay', WORD),
        ('wHour', WORD),
        ('wMinute', WORD),
        ('wSecond', WORD),
        ('wMilliseconds', WORD)]

    def __repr__(self):
        days = ('Su','Mo','Tu','We','Th','Fr','Sa')
        return 'SYSTEMTIME(%04d.%02d.%02d [%s] %02d:%02d:%02d.%03d)' % (
            self.wYear, self.wMonth, self.wDay, days[self.wDayOfWeek],
            self.wHour, self.wMinute, self.wSecond, self.wMilliseconds)


class FILETIME(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('dwLowDateTime', DWORD),
        ('dwHighDateTime', DWORD)]

    def __repr__(self):
        return 'FILETIME(%d)' % (self.getvalue())
    
    def getvalue(self):
        """Get the underline uint64."""
        return self.dwLowDateTime + (self.dwHighDateTime << 32)

    def setvalue(self, n):
        """Set the underline uint64."""
        self.dwLowDateTime = n & 0xffffffff
        self.dwHighDateTime = (n >> 32) & 0xffffffff

    value = property(getvalue, setvalue, None, '64-bit value')        


class TIME_ZONE_INFORMATION(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('Bias', LONG),
        ('StandardName', WCHAR * 32),
        ('StandardDate', SYSTEMTIME),
        ('StandardBias', LONG),
        ('DaylightName', WCHAR * 32),
        ('DaylightDate', SYSTEMTIME),
        ('DaylightBias', LONG)]

    def __repr__(self):
        raise NotImplementedError()


kernel32 = SharedLib.WinLib('kernel32')
LPFILETIME = ctypes.POINTER(FILETIME)
LPSYSTEMTIME = ctypes.POINTER(SYSTEMTIME)
LPTIME_ZONE_INFORMATION = ctypes.POINTER(TIME_ZONE_INFORMATION)


_FileTimeToSystemTime = kernel32('FileTimeToSystemTime',
    BOOL, [LPFILETIME, LPSYSTEMTIME])
_SystemTimeToFileTime = kernel32('SystemTimeToFileTime',
    BOOL, [LPSYSTEMTIME, LPFILETIME])
_FileTimeToLocalFileTime = kernel32('FileTimeToLocalFileTime', 
    BOOL, [LPFILETIME, LPFILETIME])
_LocalFileTimeToFileTime = kernel32('LocalFileTimeToFileTime', 
    BOOL, [LPFILETIME, LPFILETIME])
_SystemTimeToTzSpecificLocalTime = kernel32('SystemTimeToTzSpecificLocalTime', 
    BOOL, [LPTIME_ZONE_INFORMATION, LPSYSTEMTIME, LPSYSTEMTIME])
_TzSpecificLocalTimeToSystemTime = kernel32('TzSpecificLocalTimeToSystemTime', 
    BOOL, [LPTIME_ZONE_INFORMATION, LPSYSTEMTIME, LPSYSTEMTIME])
_DosDateTimeToFileTime = kernel32('DosDateTimeToFileTime',
    BOOL, [WORD, WORD, LPFILETIME])
_FileTimeToDosDateTime = kernel32('FileTimeToDosDateTime',
    BOOL, [LPFILETIME, LPWORD, LPWORD])
_CompareFileTime = kernel32('CompareFileTime',
    LONG, [LPFILETIME, LPFILETIME])
_GetTickCount = kernel32('GetTickCount',
    DWORD, [])
_GetTickCount64 = kernel32('GetTickCount64',
    ULONGLONG, [])
_GetSystemTimes = kernel32('GetSystemTimes',
    BOOL, [LPFILETIME, LPFILETIME, LPFILETIME])


def toLocalFileTime(ft):
    ret = FILETIME()
    if not _FileTimeToLocalFileTime(ft, ret):
        raise ctypes.WinError()
    return ret
    
def pythonEpochToFileTime():
    epoch = time.gmtime(0)
    st = SYSTEMTIME()
    st.wYear = epoch.tm_year
    st.wMonth = epoch.tm_mon
    st.wDay = epoch.tm_mday
    st.wHour = epoch.tm_hour
    st.wMinute = epoch.tm_min
    st.wSecond = epoch.tm_sec
    st.wMilliseconds = 0
    ft = FILETIME()
    if not _SystemTimeToFileTime(st, ft):
        raise ctypes.WinError()
    return ft


def test():
    ft = FILETIME(0)
    st = SYSTEMTIME()
    _FileTimeToSystemTime(ft, st)
    print 'Windows epoch:', st

    #pyEpochDelta = long(pythonEpochToFileTime())
    pyEpochDelta = pythonEpochToFileTime().getvalue()
    print 'Python epoch delta:', pyEpochDelta

    #x = long(FILETIME(0, 0)) + pyEpochDelta
    x = FILETIME(0, 0).getvalue() + pyEpochDelta
    #ft.init(x)
    ft.setvalue(x)
    _FileTimeToSystemTime(ft, st)
    print 'Python epoch:', st
    

if __name__ == '__main__':
    test()

'''
implemented:
    FileTimeToLocalFileTime / LocalFileTimeToFileTime
    FileTimeToSystemTime / SystemTimeToFileTime
    FileTimeToDosDateTime / DosDateTimeToFileTime
    SystemTimeToTzSpecificLocalTime / TzSpecificLocalTimeToSystemTime
    CompareFileTime
    GetTickCount
    GetTickCount64
    GetSystemTimes
pending:
    GetDynamicTimeZoneInformation / SetDynamicTimeZoneInformation
    GetFileTime / SetFileTime
    GetLocalTime / SetLocalTime
    GetSystemTime / SetSystemTime
    GetSystemTimeAsFileTime
    GetSystemTimeAdjustment / SetSystemTimeAdjustment
    GetTimeZoneInformation / SetTimeZoneInformation
    GetTimeZoneInformationForYear
    GetTimeFormat
    NtQuerySystemTime
    RtlLocalTimeToSystemTime
    RtlTimeToSecondsSince1970
'''


def FileTimeToSystemTime(ft):
    st = SYSTEMTIME()
    if not _FileTimeToSystemTime(ft, st):
        raise ctypes.WinError()
    return st


def SystemTimeToFileTime(st):
    ft = FILETIME()
    if not _SystemTimeToFileTime(st, ft):
        raise ctypes.WinError()
    return ft


def FileTimeToLocalFileTime(ft):
    lft = FILETIME()
    if not _FileTimeToLocalFileTime(ft, lft):
        raise ctypes.WinError()
    return lft


def LocalFileTimeToFileTime(lft):
    ft = FILETIME()
    if not _LocalFileTimeToFileTime(lft, ft):
        raise ctypes.WinError()
    return ft
    

def SystemTimeToTzSpecificLocalTime(tz, st):
    lst = SYSTEMTIME()
    if not _SystemTimeToTzSpecificLocalTime(tz, st, lst):
        raise ctypes.WinError()
    return lst


def TzSpecificLocalTimeToSystemTime(tz, lst):
    st = SYSTEMTIME()
    if not _TzSpecificLocalTimeToSystemTime(tz, lst, st):
        raise ctypes.WinError()
    return st


##from ctypes.wintypes import BOOLEAN, LARGE_INTEGER, ULONG
##PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)
##PULONG = ctypes.POINTER(ULONG)
##
##ntdll = SharedLib.WinLib('ntdll')
##RtlTimeToSecondsSince1970 = ntdll('RtlTimeToSecondsSince1970', BOOLEAN, [PLARGE_INTEGER, PULONG])


def DosDateTimeToFileTime(date, time):
    ft = FILETIME()
    if not _DosDateTimeToFileTime(date, time, ft):
        raise ctypes.WinError()
    return ft


def FileTimeToDosDateTime(ft):
    date, time = DWORD(), DWORD()
    if not _FileTimeToDosDateTime(ft, date, time):
        raise ctypes.WinError()
    return date, time


def CompareFileTime(ft1, ft2):
    return _CompareFileTime(ft1, ft2)


def GetTickCount():
    return _GetTickCount()


def GetTickCount64():
    return _GetTickCount64()


def GetSystemTimes():
    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    if not _GetSystemTimes(idle, kernel, user):
        raise ctypes.WinError()
    return idle, kernel, user


##BOOL WINAPI GetFileTime(
##  __in       HANDLE hFile,
##  __out_opt  LPFILETIME lpCreationTime,
##  __out_opt  LPFILETIME lpLastAccessTime,
##  __out_opt  LPFILETIME lpLastWriteTime
##);
##
##BOOL WINAPI SetFileTime(
##  __in      HANDLE hFile,
##  __in_opt  const FILETIME* lpCreationTime,
##  __in_opt  const FILETIME* lpLastAccessTime,
##  __in_opt  const FILETIME* lpLastWriteTime
##);
