"""Windows date/time functions."""

from __future__ import division

import ctypes
import datetime
import contextlib
import time

import dllutil

from ctypes.wintypes import BOOL, WORD, DWORD, LONG, WCHAR, HANDLE
LPWORD = ctypes.POINTER(WORD)
ULONGLONG = ctypes.c_uint64

from win32con import OPEN_EXISTING
# constants missing from win32con
FILE_READ_ATTRIBUTES = 0x0080
FILE_WRITE_ATTRIBUTES = 0x0100


class FILETIME(ctypes.Structure):
    _fields_ = [
        ('dwLowDateTime', DWORD),
        ('dwHighDateTime', DWORD)]

    def __repr__(self):
        return 'FILETIME({0!r},{1!r})'.format(self.dwLowDateTime, self.dwHighDateTime)
    
##    def getvalue(self):
##        """Get the underline uint64."""
##        return self.dwLowDateTime + (self.dwHighDateTime << 32)
##
##    def setvalue(self, n):
##        """Set the underline uint64."""
##        self.dwLowDateTime = n & 0xffffffff
##        self.dwHighDateTime = (n >> 32) & 0xffffffff
##
##    value = property(getvalue, setvalue, None, '64-bit value')        


class SYSTEMTIME(ctypes.Structure):
    _fields_ = [('wYear', WORD),
                ('wMonth', WORD),
                ('wDayOfWeek', WORD),
                ('wDay', WORD),
                ('wHour', WORD),
                ('wMinute', WORD),
                ('wSecond', WORD),
                ('wMilliseconds', WORD)]

    def __repr__(self):
        return 'SYSTEMTIME({0!r},{1!r},{2!r},{3!r},{4!r},{5!r},{6!r},{7!r})'.format(
            self.wYear, self.wMonth, self.wDayOfWeek, self.wDay,
            self.wHour, self.wMinute, self.wSecond, self.wMilliseconds)

##    def __str__(self):
##        days = ('Su','Mo','Tu','We','Th','Fr','Sa')
##        return 'SYSTEMTIME(%04d.%02d.%02d [%s] %02d:%02d:%02d.%03d)' % (
##            self.wYear, self.wMonth, self.wDay, days[self.wDayOfWeek],
##            self.wHour, self.wMinute, self.wSecond, self.wMilliseconds)

class TIME_ZONE_INFORMATION(ctypes.Structure):
    _fields_ = [('Bias', LONG),
                ('StandardName', WCHAR * 32),
                ('StandardDate', SYSTEMTIME),
                ('StandardBias', LONG),
                ('DaylightName', WCHAR * 32),
                ('DaylightDate', SYSTEMTIME),
                ('DaylightBias', LONG)]

    def __repr__(self):
        return 'TIME_ZONE_INFORMATION({0!r},{1!r},{2!r},{3!r},{4!r},{5!r},{6!r})'.format(
            self.Bias,
            self.StandardName, self.StandardDate, self.StandardBias,
            self.DaylightName, self.DaylightDate, self.DaylightBias)
        

LPFILETIME = ctypes.POINTER(FILETIME)
LPSYSTEMTIME = ctypes.POINTER(SYSTEMTIME)
LPTIME_ZONE_INFORMATION = ctypes.POINTER(TIME_ZONE_INFORMATION)

kernel32 = dllutil.WinDLL('kernel32')

FileTimeToLocalFileTime = kernel32('FileTimeToLocalFileTime', BOOL, [LPFILETIME, LPFILETIME])
LocalFileTimeToFileTime = kernel32('LocalFileTimeToFileTime', BOOL, [LPFILETIME, LPFILETIME])
FileTimeToSystemTime = kernel32('FileTimeToSystemTime', BOOL, [LPFILETIME, LPSYSTEMTIME])
SystemTimeToFileTime = kernel32('SystemTimeToFileTime', BOOL, [LPSYSTEMTIME, LPFILETIME])
SystemTimeToTzSpecificLocalTime = kernel32('SystemTimeToTzSpecificLocalTime', BOOL, [LPTIME_ZONE_INFORMATION, LPSYSTEMTIME, LPSYSTEMTIME])
TzSpecificLocalTimeToSystemTime = kernel32('TzSpecificLocalTimeToSystemTime', BOOL, [LPTIME_ZONE_INFORMATION, LPSYSTEMTIME, LPSYSTEMTIME])

FileTimeToDosDateTime = kernel32('FileTimeToDosDateTime', BOOL, [LPFILETIME, LPWORD, LPWORD])
DosDateTimeToFileTime = kernel32('DosDateTimeToFileTime', BOOL, [WORD, WORD, LPFILETIME])
CompareFileTime = kernel32('CompareFileTime', LONG, [LPFILETIME, LPFILETIME])
GetTickCount = kernel32('GetTickCount', DWORD, [])
try:
    GetTickCount64 = kernel32('GetTickCount64', ULONGLONG, [])
except AttributeError:
    GetTickCount64 = None
GetFileTime = kernel32('GetFileTime', BOOL, [HANDLE, LPFILETIME, LPFILETIME, LPFILETIME])
SetFileTime = kernel32('SetFileTime', BOOL, [HANDLE, LPFILETIME, LPFILETIME, LPFILETIME])
GetSystemTimes = kernel32('GetSystemTimes', BOOL, [LPFILETIME, LPFILETIME, LPFILETIME])



def filetime_utc_to_local(ft, tzinfo=True):
    """Convert a Windows FILETIME from UTC to local.

    'tzinfo' can specify a TIME_ZONE_INFORMATION for more accurate results.
    The default value of True represents the current time zone settings.
    If set to False the conversion is done faster but less accurately.
    """
    ret = FILETIME()
    if not tzinfo:
        if not FileTimeToLocalFileTime(ft, ret):
            raise ctypes.WinError()
    else:
        st, lst = SYSTEMTIME(), SYSTEMTIME()
        if tzinfo is True:
            tzinfo = None
        if not FileTimeToSystemTime(ft, st) or \
           not SystemTimeToTzSpecificLocalTime(tzInfo, st, lst) or \
           not SystemTimeToFileTime(lst, ret):
                raise ctypes.WinError()
    return ret


def filetime_local_to_utc(ft, tzinfo=True):
    """Convert a Windows FILETIME from local to UTC.

    'tzinfo' can specify a TIME_ZONE_INFORMATION for more accurate results.
    The default value of True represents the current time zone settings.
    If set to False the conversion is done faster but less accurately.
    """
    ret = FILETIME()
    if not tzinfo:
        if not LocalFileTimeToFileTime(ft, ret):
            raise ctypes.WinError()
    else:
        st, lst = SYSTEMTIME(), SYSTEMTIME()
        if tzinfo is True:
            tzinfo = None
        if not FileTimeToSystemTime(ft, st) or \
           not TzSpecificLocalTimeToSystemTime(tzinfo, st, lst) or \
           not SystemTimeToFileTime(lst, ret):
                raise ctypes.WinError()
    return ret


_FILETIME_null_date = datetime.datetime(1601, 1, 1, 0, 0, 0)
def filetime_to_datetime(ft):
    """Convert a Windows FILETIME to a Python datetime.

    From Julian Rath's "Recipe 511425: FILETIME to datetime (Python)"
    http://code.activestate.com/recipes/511425-filetime-to-datetime/
    """
    microseconds = (ft.dwLowDateTime | (ft.dwHighDateTime << 32)) // 10
    return _FILETIME_null_date + datetime.timedelta(microseconds=microseconds)


def python_epoch_utc_to_filetime():
    """Get the FILETIME of Python's time epoch."""
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
    if not SystemTimeToFileTime(st, ft):
        raise ctypes.WinError()
    return ft


def filetime_to_systemtime(ft):
    """Convert a FILETIME to SYSTEMTIME."""
    st = SYSTEMTIME()
    if not FileTimeToSystemTime(ft, st):
        raise ctypes.WinError()
    return st


def systemtime_to_filetime(st):
    """Convert a SYSTEMTIME to FILETIME."""
    ft = FILETIME()
    if not SystemTimeToFileTime(st, ft):
        raise ctypes.WinError()
    return ft


def systemtime_utc_to_local(st, tz=None):
    """Convert a SYSTEMTIME from UTC to a time-zone specific local."""
    lst = SYSTEMTIME()
    if not SystemTimeToTzSpecificLocalTime(tz, st, lst):
        raise ctypes.WinError()
    return lst


def systemtime_local_to_utc(lst, tz=None):
    """Convert a SYSTEMTIME from a time-zone specific local to UTC."""
    st = SYSTEMTIME()
    if not TzSpecificLocalTimeToSystemTime(tz, lst, st):
        raise ctypes.WinError()
    return st


##from ctypes.wintypes import BOOLEAN, LARGE_INTEGER, ULONG
##PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)
##PULONG = ctypes.POINTER(ULONG)
##
##ntdll = dllutil.WinDLL('ntdll')
##RtlTimeToSecondsSince1970 = ntdll('RtlTimeToSecondsSince1970', BOOLEAN, [PLARGE_INTEGER, PULONG])


def dosdatetime_to_filetime(date, time):
    """Convert a DOS datetime (WORD pair) to a FILETIME."""
    ft = FILETIME()
    if not _DosDateTimeToFileTime(date, time, ft):
        raise ctypes.WinError()
    return ft


def filetime_to_dosdatetime(ft):
    """Convert a FILETIME to a DOS datetime (WORD pair)."""
    date, time = DWORD(), DWORD()
    if not FileTimeToDosDateTime(ft, date, time):
        raise ctypes.WinError()
    return date, time


def compare_filetime(ft1, ft2):
    """Compare two FILETIMEs and return -1/0/1."""
    return CompareFileTime(ft1, ft2)


def get_tick_count(bits=32, fallback=False):
    """Get uptime msec (32 or 64-bit).

    If fallback is true and the 64-bit counter is not available, the 32-bit one is returned.
    """
    if bits == 32:
        return GetTickCount()
    elif bits == 64:
        if GetTickCount64:
            return GetTickCount64()
        elif fallback:
            return GetTickCount()
        else:
            raise NotImplementedError('64-bit tick counter is not available')
    else:
        raise ValueError('invalid bit value; must be 32 or 64')


def get_file_time(f):
    """Get the create/access/modify FILETIMEs of a file (Py)HANDLE or path."""
    created, accessed, modified = FILETIME(), FILETIME(), FILETIME()
    if isinstance(f, basestring):
        with contextlib.closing(win32file.CreateFileW(f, FILE_READ_ATTRIBUTES, 0, None, OPEN_EXISTING, 0, None)) as h:
            if not GetFileTime(h.handle, created, accessed, modified):
                raise ctypes.WinError()
    elif not GetFileTime(int(f), created, accessed, modified):
        raise ctypes.WinError()
    return created, accessed, modified


def set_file_time(f, created=None, accessed=None, modified=None):
    """Set the create/access/modify FILETIMEs of a file (Py)HANDLE or path."""
    if isinstance(f, basestring):
        with contextlib.closing(win32file.CreateFileW(f, FILE_WRITE_ATTRIBUTES, 0, None, OPEN_EXISTING, 0, None)) as h:
            if not SetFileTime(h.handle, created, accessed, modified):
                raise ctypes.WinError()
    elif not SetFileTime(int(f), created, accessed, modified):
        raise ctypes.WinError()


def get_system_times():
    """Get idle, kernel and user FILETIMEs."""
    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    if not GetSystemTimes(idle, kernel, user):
        raise ctypes.WinError()
    return idle, kernel, user


# TODO: pending:
#    GetDynamicTimeZoneInformation / SetDynamicTimeZoneInformation
#    GetFileTime / SetFileTime
#    GetLocalTime / SetLocalTime
#    GetSystemTime / SetSystemTime
#    GetSystemTimeAsFileTime
#    GetSystemTimeAdjustment / SetSystemTimeAdjustment
#    GetTimeZoneInformation / SetTimeZoneInformation
#    GetTimeZoneInformationForYear
#    GetTimeFormat
#    NtQuerySystemTime
#    RtlLocalTimeToSystemTime
#    RtlTimeToSecondsSince1970
