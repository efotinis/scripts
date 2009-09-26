"""Misc window utilities."""

import ctypes
import win32gui, win32process, win32process, win32con
import SharedLib
from ctypes.wintypes import BOOL, UINT, LONG, LPVOID


class RECT(ctypes.Structure):
    _fields_ = [
        ('left', LONG),
        ('top', LONG),
        ('right', LONG),
        ('bottom', LONG),
    ]
    def __init__(self, init=None):
        """Initializer can be:
        - a 4-item sequence (left,top,right,bottom)
        - another RECT
        - None (init to zeroes)
        """
        try:
            if len(init) != 4:
                raise ValueError
            self.left, self.top, self.right, self.bottom = init
        except (TypeError, ValueError):
            try:
                self.left = init.left
                self.top = init.top
                self.right = init.right
                self.bottom = init.bottom
            except AttributeError:
                self.left = 0
                self.top = 0
                self.right = 0
                self.bottom = 0
    def width(self):
        return self.right - self.left
    def height(self):
        return self.bottom - self.top
    def offset(self, dx, dy):
        self.left += dx
        self.right += dx
        self.top += dy
        self.bottom += dy
LPRECT = ctypes.POINTER(RECT)


user32 = SharedLib.WinLib('user32')
SystemParametersInfoW = user32('SystemParametersInfoW', BOOL, [UINT,UINT,PVOID,UINT])
AdjustWindowRectEx = user32('AdjustWindowRectEx', BOOL, [LPRECT,DWORD,BOOL,DWORD])


def genDesktopWnds(cls=None, title=None):
    """Generate the handles of top level windows with a specific class/title."""
    cur = 0
    while True:
        cur = win32gui.FindWindowEx(0, cur, cls, title)
        if cur:
            yield cur
        else:
            break


def genChildWnds(wnd):
    """Generate the handles of a window's children."""
    cur = win32gui.GetWindow(wnd, win32con.GW_CHILD)
    while cur:
        yield cur
        cur = win32gui.GetWindow(cur, win32con.GW_HWNDNEXT)


def getTopOwnerWnd(wnd):
    """Find the top-most owner of a window."""
    while wnd:
        owner = win32gui.GetParent(wnd)
        if owner:
            wnd = owner
        else:
            break
    return wnd


def getWndProcId(w):
    """Get the process ID of a window.
    
    Fixes a bug in win32process.GetWindowThreadProcessId,
    where a random proc ID is returned on error.
    """
    thread, proc = win32process.GetWindowThreadProcessId(w)
    return proc if thread else 0  # thread==0 means error


def getWorkarea():
    """Get the current workarea as a RECT.

    Needed because SPI_GETWORKAREA is not implemented in
    win32gui.SystemParametersInfo (pywin v2.5.210).
    """
    wa = RECT()
    if not SystemParametersInfoW(win32con.SPI_GETWORKAREA, 0, ctypes.byref(wa), 0):
        raise WindowsError
    return wa


def adjustWndRect(rc, wnd):
    """Adjust client rect to window rect, using a wnd's current styles/menu.

    Note: pywin (v2.5.210) doesn't include AdjustWindowRect(Ex).
    """
    style = win32gui.GetWindowLong(wnd, win32con.GWL_STYLE)
    hasmenu = win32gui.GetMenu(wnd)
    exstyle = win32gui.GetWindowLong(wnd, win32con.GWL_EXSTYLE)
    tmp = RECT(rc)  # prevent modify of original
    if not AdjustWindowRectEx(ctypes.byref(tmp), style, hasmenu, exstyle):
        raise WindowsError
    return tmp


def moveWnd(wnd, rc):
    """Move window to specified screen rect and repaint."""
    win32gui.MoveWindow(wnd, rc.left, rc.top, rc.width(), rc.height(), True)


