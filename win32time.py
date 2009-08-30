import time
import ctypes
import SharedLib
from ctypes.wintypes import BOOL, WORD, DWORD, LONG, WCHAR


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

##    def __long__(self):
##        return self.dwLowDateTime + (self.dwHighDateTime << 32)

##    def init(self):
##        self.dwLowDateTime = n & 0xffffffff
##        self.dwHighDateTime = (n >> 32) & 0xffffffff
##

    def __repr__(self):
        return 'FILETIME(low=%d, high=%d)' % (self.dwLowDateTime, self.dwHighDateTime)
    
    def getvalue(self):
        return self.dwLowDateTime + (self.dwHighDateTime << 32)

    def setvalue(self, n):
        self.dwLowDateTime = n & 0xffffffff
        self.dwHighDateTime = (n >> 32) & 0xffffffff


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
    CompareFileTime
    DosDateTimeToFileTime
    FileTimeToDosDateTime
x   FileTimeToLocalFileTime
x   FileTimeToSystemTime
    GetDynamicTimeZoneInformation
    GetFileTime
    GetLocalTime
    GetSystemTime
    GetSystemTimeAdjustment
    GetSystemTimeAsFileTime
    GetSystemTimes
    GetTickCount
    GetTickCount64
    GetTimeFormat
    GetTimeZoneInformation
    GetTimeZoneInformationForYear
x   LocalFileTimeToFileTime
    NtQuerySystemTime
    RtlLocalTimeToSystemTime
    RtlTimeToSecondsSince1970
    SetDynamicTimeZoneInformation
    SetFileTime
    SetLocalTime
    SetSystemTime
    SetSystemTimeAdjustment
    SetTimeZoneInformation
x   SystemTimeToFileTime
x   SystemTimeToTzSpecificLocalTime
x   TzSpecificLocalTimeToSystemTime
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
    if not _TzSpecificLocalTimeToSystemTime (tz, lst, st):
        raise ctypes.WinError()
    return st


##from ctypes.wintypes import BOOLEAN, LARGE_INTEGER, ULONG
##PLARGE_INTEGER = ctypes.POINTER(LARGE_INTEGER)
##PULONG = ctypes.POINTER(ULONG)
##
##ntdll = SharedLib.WinLib('ntdll')
##RtlTimeToSecondsSince1970 = ntdll('RtlTimeToSecondsSince1970', BOOLEAN, [PLARGE_INTEGER, PULONG])
