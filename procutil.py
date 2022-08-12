import ctypes
import struct

import win32api
import win32process
import win32con

import dllutil

from ctypes.wintypes import LPVOID, LPCVOID, HANDLE, DWORD, BOOL
LPDWORD = ctypes.POINTER(DWORD)


kernel32 = dllutil.WinDLL('kernel32')
VirtualAllocEx = kernel32('VirtualAllocEx', LPVOID, [HANDLE,LPVOID,DWORD,DWORD,DWORD])
VirtualFreeEx = kernel32('VirtualFreeEx', BOOL, [HANDLE,LPVOID,DWORD,DWORD])
ReadProcessMemory = kernel32('ReadProcessMemory', BOOL, [HANDLE,LPCVOID,LPVOID,DWORD,LPDWORD])
WriteProcessMemory = kernel32('WriteProcessMemory', BOOL, [HANDLE,LPVOID,LPCVOID,DWORD,LPDWORD])


class WindowProcess:
    """Represents the process of a window."""
    def __init__(self, hwnd):
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        self.proc = win32api.OpenProcess(
            win32con.PROCESS_VM_OPERATION |
            win32con.PROCESS_VM_READ |
            win32con.PROCESS_VM_WRITE,
            False, pid)
    def close(self):
        if self.proc is not None:
            self.proc.close()
            self.proc = None
    def __del__(self):
        self.close()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    def __int__(self):
        """Process handle (int)."""
        return self.proc.handle


class ProcessMemory:
    """Manage memory in a foreign process."""

    def __init__(self, proc, size):
        """Accept a pid or PyHANDLE."""
        self.proc = HANDLE(int(proc))
        self.size = size
        self.mem = VirtualAllocEx(self.proc, 0, size,
                                  win32con.MEM_RESERVE | win32con.MEM_COMMIT,
                                  win32con.PAGE_READWRITE);
        if not self.mem:
            raise WindowsError('VirtualAllocEx failed')

    def close(self):
        if self.mem is not None:
            VirtualFreeEx(self.proc, self.mem, 0, win32con.MEM_RELEASE)
            self.mem = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def ptr(self):
        """Get raw pointer (sometimes needed for pointer fields)."""
        return self.mem

    def __len__(self):
        return self.size

    def _rangecheck(self, pos, size):
        """Throw if a pos/size pair is out of range."""
        if pos < 0 or pos + size > self.size:
            raise ValueError('out of range', pos, size, self.size)

    def read(self, pos=None, size=None):
        """Read raw data as a binary string."""
        if pos is None:
            pos = 0
        if size is None:
            size = self.size - pos
        self._rangecheck(pos, size)
        buf = ctypes.create_string_buffer(size)
        if not ReadProcessMemory(self.proc, self.mem + pos, buf, size, None):
            raise WindowsError('ReadProcessMemory failed')
        return buf.raw

    def write(self, s, pos=None):
        """Write raw data as a binary string."""
        if pos is None:
            pos = 0
        self._rangecheck(pos, len(s))
        buf = ctypes.create_string_buffer(s)
        if not WriteProcessMemory(self.proc, self.mem + pos, buf, len(s), None):
            raise WindowsError('WriteProcessMemory failed')

    def read_pstruct(self, pos, fmt):
        """Read packed structure data."""
        s = self.read(pos, struct.calcsize(fmt))
        return struct.unpack(fmt, s)

    def write_pstruct(self, pos, fmt, *items):
        """Write packed structure data."""
        s = struct.pack(fmt, *items)
        self.write(s, pos)

    def read_cstruct(self, pos, obj):
        """Read ctypes.Structure object."""
        size = ctypes.sizeof(obj)
        s = self.read(pos, size)
        ctypes.memmove(obj, s, size)

    def write_cstruct(self, pos, obj):
        """Write ctypes.Structure object."""
        size = ctypes.sizeof(obj)
        s = ctypes.string_at(ctypes.addressof(obj), size)
        self.write(s, pos)

    def read_str_buf(self, pos=None, size=None):
        """Read a zero-terminated buffer string; return whole buffer if there's no terminator."""
        s = self.read(pos, size)
        try:
            return s[:s.index('\0')]
        except ValueError:
            return s

    def read_unicode_buf(self, pos=None, size=None):
        """Read a zero-terminated buffer unicode string; return whole buffer if there's no terminator."""
        s = self.read(pos, size).decode('utf_16le')
        try:
            return s[:s.index('\0')]
        except ValueError:
            return s
