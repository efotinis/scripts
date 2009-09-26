import win32evtlog
import win32evtlogutil
import ctypes
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPVOID
LPDWORD = ctypes.POINTER(DWORD)


class Reader:

    # TODO: RegisterEventSource, DeregisterEventSource, ReportEvent

    # handy consts (saves user for having to import win32evtlog)
    FORWARD = win32evtlog.EVENTLOG_FORWARDS_READ
    BACKWARD = win32evtlog.EVENTLOG_BACKWARDS_READ

    # getInfo() setup
    GetEventLogInformation = ctypes.windll.advapi32.GetEventLogInformation
    GetEventLogInformation.restype = BOOL
    GetEventLogInformation.argtypes = [HANDLE,DWORD,LPVOID,DWORD,LPDWORD]
    EVENTLOG_FULL_INFO = 0
    class EVENTLOG_FULL_INFORMATION(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ('dwFull', DWORD)]
    # map an info type (eg. EVENTLOG_FULL_INFO)
    # to a structure type and its size (eg. (EVENTLOG_FULL_INFORMATION, 4))
    infoStructMap = {
        EVENTLOG_FULL_INFO: (EVENTLOG_FULL_INFORMATION, 4)}


    def __init__(self):
        """Read access to a log."""
        self.handle = None

    def __del__(self):
        self.close()

    def openLive(self, source, server=None):
        """Open a live log. Use server=None for local machine."""
        self.close()
        self.handle = win32evtlog.OpenEventLog(server, source)

    def openBackup(self, fname, server=None):
        """Open a saved log. Use server=None for local machine or when fname is remote."""
        self.close()
        self.handle = win32evtlog.OpenBackupEventLog(server, fname)

    def isOpen(self):
        return self.handle is not None

    def close(self):
        """Close log if open."""
        if self.isOpen():
            win32evtlog.CloseEventLog(self.handle)
            self.handle = None

    def backup(self, fname):
        """Save log to a file. Also works with backups."""
        win32evtlog.BackupEventLog(self.handle, fname)

    def clear(self, fname=None):
        """Clear log and optionally save events to a file. Does not work with backups."""
        win32evtlog.ClearEventLog(self.handle, fname)

    def getOldest(self):
        """Get the recno of the oldest event."""
        return win32evtlog.GetOldestEventLogRecord(self.handle)

    def getCount(self):
        """Get the count of events."""
        return win32evtlog.GetNumberOfEventLogRecords(self.handle)

    def notifyChange(self, eventObj):
        """Signal eventObj when log is written to. Only works on local logs."""
        win32evtlog.NotifyChangeEventLog(self.handle, eventObj)

    def read(self, flags, recno=None):
        """Return a list of one or more records (empty on end).

        If recno is None, read sequentially.
        """
        if recno is None:
            flags |= win32evtlog.EVENTLOG_SEQUENTIAL_READ
            recno = 0  # to make ReadEventLog happy
        else:
            flags |= win32evtlog.EVENTLOG_SEEK_READ
        return win32evtlog.ReadEventLog(self.handle, flags, recno)

    def getInfo(self, type):
        """Get info structure of specified type."""
        info, infoSize = self.infoStructMap[type]
        info = info()
        bytesNeeded = self.DWORD()
        ok = self.GetEventLogInformation(self.handle,
            type, ctypes.byref(info), infoSize, ctypes.byref(bytesNeeded))
        if not ok:
            raise WindowsError
        return info
            
    def isFull(self):
        """Return whether log is full."""
        return bool(self.getInfo(self.EVENTLOG_FULL_INFO).dwFull)


    # context management (with stmt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


    # iteration

    class _Iter:

        def __init__(self, log, dirFlag):
            self.log = log
            self.dirFlag = dirFlag
            self.queue = []

        def __iter__(self):
            return self

        def next(self):
            if not self.queue:
                self.queue = self.log.read(self.dirFlag)
                if not self.queue:
                    raise StopIteration
            return self.queue.pop(0)

    def iter(self):
        """Forward iterator."""
        return self._Iter(self, win32evtlog.EVENTLOG_FORWARDS_READ)

    def riter(self):
        """Backward iterator."""
        return self._Iter(self, win32evtlog.EVENTLOG_BACKWARDS_READ)


# convenience classes
class LiveReader(Reader):
    def __init__(self, source, server=None):
        """Read access for a live log."""
        Reader.__init__(self)
        self.openLive(source, server)
class BackupReader(Reader):
    def __init__(self, name, server=None):
        """Read access for a saved log."""
        Reader.__init__(self)
        self.openBackup(name, server)


class Source:

    def __init__(self, appName, server=None):
        """Add events to a live log."""
        self.handle = None  # init
        self.handle = win32evtlogutil.RegisterEventSource(server, appName)

    def __del__(self):
        self.close()

    def isOpen(self):
        return self.handle is not None

    def close(self):
        if self.isOpen():
            win32evtlogutil.DeregisterEventSource(self.handle)
            self.handle = None

    def report(self, eventID, eventCategory=0, eventType=win32evtlog.EVENTLOG_ERROR_TYPE, strings=None, data=None, sid=None):
        win32evtlog.ReportEvent(self.handle, eventType, eventCategory,
                                eventID, sid, strings, data)


    # context management (with stmt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def _padToDword(n):
    """Increase n if needed to match a multiple of DWORD size."""
    return (n + 3) & ~3


# TODO: check this
def recSize(e):
    """Calc record size of specified event."""
    n = 12*4 + 4*2  # fixed fields
    n += 2 * (len(e.SourceName) + 1)
    n += 2 * (len(e.ComputerName) + 1)
    n = _padToDword(n)
    if e.Sid:
        n += len(buffer(e.Sid))
    if e.StringInserts:
        n += sum(2*(len(s)+1) for s in e.StringInserts)
    n += len(e.Data)
    n = _padToDword(n)
    n += 4  # trailing size
    return n    
