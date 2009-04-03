from __future__ import with_statement
import re, ctypes
import win32api, win32process, win32gui, win32con
import SharedLib, WinUtil


LPVOID = LPCVOID = ctypes.c_void_p
HANDLE = LPVOID
DWORD = ctypes.c_ulong
LPDWORD = ctypes.POINTER(DWORD)
BOOL = ctypes.c_int
kernel32 = SharedLib.WinLib('kernel32')
VirtualAllocEx = kernel32('VirtualAllocEx', LPVOID, [HANDLE,LPVOID,DWORD,DWORD,DWORD])
VirtualFreeEx = kernel32('VirtualFreeEx', BOOL, [HANDLE,LPVOID,DWORD,DWORD])
ReadProcessMemory = kernel32('ReadProcessMemory', BOOL, [HANDLE,LPCVOID,LPVOID,DWORD,LPDWORD])


class error(Exception):
    def __init__(self, x):
        Exception.__init__(self, x)


class WindowProcess:
    """Represents the process of a window."""
    def __init__(self, hwnd):
        threadid, procid = win32process.GetWindowThreadProcessId(hwnd)
        self.proc = win32api.OpenProcess(
            win32con.PROCESS_VM_OPERATION |
            win32con.PROCESS_VM_READ |
            win32con.PROCESS_VM_WRITE,
            False, procid)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.proc.close()
    def handle(self):
        """Returns a PyHANDLE"""
        return self.proc


class ProcessMemory:
    """Manage memory in a foreign process."""
    def __init__(self, proc, size):
        self.proc = proc
        self.size = size
        self.mem = VirtualAllocEx(proc, 0, size, win32con.MEM_COMMIT, win32con.PAGE_READWRITE);
        if not self.mem:
            raise WindowsError('VirtualAllocEx failed')
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    def close(self):
        VirtualFreeEx(self.proc, self.mem, 0, win32con.MEM_RELEASE)
    def pointer(self):
        return self.mem
##    SIZE_T size() const {
##        return size_;
##    }
    def read(self):
        buf = ctypes.create_string_buffer(self.size)
        if not ReadProcessMemory(self.proc, self.mem, buf, self.size, None):
            raise WindowsError('ReadProcessMemory failed')
        return buf.value
##    template <typename T>
##    void write(int offset, T t) {
##        if (!WriteProcessMemory(proc, (char*)mem + offset, &t, sizeof(t), 0))
##            raiseWinError(_T("ProcMem::write: WriteProcessMemory"));
##    }
##private:
##    HANDLE proc;
##    SIZE_T size_;
##    void* mem;
##};


SB_GETTEXTA = win32con.WM_USER+2
SB_GETTEXTW = win32con.WM_USER+13

utorrentClassRx = re.compile(ur'^\u00b5Torrent[0-9A-Fa-f]{12}$')

def findUTorrentWnd():
    """Search main uTorrent window by its classname.
    Return 0 on error."""
    for w in WinUtil.genDesktopWnds():
        cls, title = win32gui.GetClassName(w), win32gui.GetWindowText(w)
        if utorrentClassRx.match(cls):
            return w
    return 0

def utorrentStatusbar():
    """Get uTorrent's statusbar handle.
    Throw on error."""
    hwnd = findUTorrentWnd()
    if not hwnd:
        raise error('could not find uTorrent window')
    if not win32gui.IsWindowVisible(hwnd):
        raise error('uTorrent window is hidden')
    if win32gui.IsIconic(hwnd):
        raise error('uTorrent window is minimized')
    hwnd = win32gui.FindWindowEx(hwnd, 0, 'msctls_statusbar32', None)
    if not hwnd:
        raise error('could not find uTorrent statusbar')
    return hwnd

def getStatus():
    statusbar = utorrentStatusbar()
    proc = WindowProcess(statusbar)
    with ProcessMemory(proc.handle().handle, 100) as mem:
        ret = win32api.SendMessage(statusbar, SB_GETTEXTA, 4, mem.pointer())
        s1 = mem.read()[:ret]
        ret = win32api.SendMessage(statusbar, SB_GETTEXTA, 5, mem.pointer())
        s2 = mem.read()[:ret]
        return s1, s2

if __name__ == '__main__':
    try:
        print getDownloadStatus()
    except (WindowsError, error), x:
        print str(x)
        
