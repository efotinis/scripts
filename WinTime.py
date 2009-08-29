import time
import ctypes

WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong
BOOL = ctypes.c_int

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
        ('wMilliseconds', WORD),
    ]
    def __str__(self):
        days = ('Su','Mo','Tu','We','Th','Fr','Sa')
        return 'SYSTEMTIME(%04d.%02d.%02d [%s] %02d:%02d:%02d.%03d)' % (
            self.wYear, self.wMonth, self.wDay, days[self.wDayOfWeek],
            self.wHour, self.wMinute, self.wSecond, self.wMilliseconds
            )

class FILETIME(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('dwLowDateTime', DWORD),
        ('dwHighDateTime', DWORD),
    ]
    def __long__(self):
        return self.dwLowDateTime + (self.dwHighDateTime << 32)
        #return long(self.dwLowDateTime & 0xffffffff) | (long(self.dwHighDateTime & 0xffffffff) << 32)
    def init(self, n):
        self.dwLowDateTime = n & 0xffffffff
        self.dwHighDateTime = (n >> 32) & 0xffffffff

FileTimeToSystemTime = ctypes.windll.kernel32.FileTimeToSystemTime
FileTimeToSystemTime.restype = BOOL
FileTimeToSystemTime.argtypes = [ctypes.POINTER(FILETIME),
                                 ctypes.POINTER(SYSTEMTIME)]

SystemTimeToFileTime = ctypes.windll.kernel32.SystemTimeToFileTime
SystemTimeToFileTime.restype = BOOL
SystemTimeToFileTime.argtypes = [ctypes.POINTER(SYSTEMTIME),
                                 ctypes.POINTER(FILETIME)]

FileTimeToLocalFileTime = ctypes.windll.kernel32.FileTimeToLocalFileTime
FileTimeToLocalFileTime.restype = BOOL
FileTimeToLocalFileTime.argtypes = [ctypes.POINTER(FILETIME),
                                    ctypes.POINTER(FILETIME)]

def toLocalFileTime(ft):
    ret = FILETIME()
    FileTimeToLocalFileTime(ctypes.byref(ft), ctypes.byref(ret))
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
    SystemTimeToFileTime(ctypes.byref(st), ctypes.byref(ft))
    return ft


def test():
    ft = FILETIME(0, 0)
    st = SYSTEMTIME()
    FileTimeToSystemTime(ft, st)
    print 'Windows epoch:', st

    pyEpochDelta = long(pythonEpochToFileTime())
    print 'Python epoch delta:', pyEpochDelta

    x = long(FILETIME(0, 0)) + pyEpochDelta
    ft.init(x)
    FileTimeToSystemTime(ft, st)
    print 'Python epoch:', st
    

if __name__ == '__main__':
    test()
    