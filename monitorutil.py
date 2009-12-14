"""Windows monitor utilities."""

import sys

import win32api
import win32gui
import win32con

import dllutil


if not hasattr(win32con, 'SPI_GETSCREENSAVESECURE'):
    setattr(win32con, 'SPI_GETSCREENSAVESECURE', 0x0076)
if not hasattr(win32con, 'SPI_SETSCREENSAVESECURE'):
    setattr(win32con, 'SPI_SETSCREENSAVESECURE', 0x0077)


def launchscreensaver():
    """Request launch of screensaver."""
    _monitorcommand(win32con.SC_SCREENSAVE, 0)


def suspendmonitor():
    """Request monitor suspension."""
    _monitorcommand(win32con.SC_MONITORPOWER, 1)


def turnoffmonitor():
    """Request monitor turn-off."""
    _monitorcommand(win32con.SC_MONITORPOWER, 2)


def _monitorcommand(wparam, lparam):
    """Post a monitor command.

    There's no way to test whether the command request is successful.
    """
    wnd = win32gui.GetForegroundWindow()
    msg = win32con.WM_SYSCOMMAND
    if not win32api.PostMessage(wnd, msg, wparam, lparam):
        # BUG: win32api.PostMessage returns 0 on success
        #raise RuntimeError('monitor command posting failed')
        pass


# patch for un-implemented options in win32gui.SystemParametersInfo
#
import ctypes
from ctypes.wintypes import BOOL, UINT
PVOID = ctypes.c_void_p
#
_user32 = dllutil.WinDLL('user32')
_SystemParametersInfoW = _user32('SystemParametersInfoW', BOOL, [UINT, UINT, PVOID, UINT])
#
def _SystemParametersInfo(action, param=None, winini=0):
    if action == win32con.SPI_GETSCREENSAVESECURE:
        param = BOOL()
        if not _SystemParametersInfoW(action, 0, ctypes.byref(param), winini):
            raise ctypes.WinError()
        return bool(param.value)
    elif action == win32con.SPI_SETSCREENSAVESECURE:
        # NOTE: VS9's MSDN says param goes to pvParam, but that's wrong; it goes to uiParam
        if not _SystemParametersInfoW(action, param, None, winini):
            raise ctypes.WinError()
    else:
        return win32gui.SystemParametersInfo(action, param, winini)
    

class _Screensaver(object):
    """Screensaver system info."""
    
    # NOTE: I wanted to make the properties class members,
    #       but that requires heavy metaclass voodoo.

    def _property(nget, nset, doc):
        flags = win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDCHANGE
        return property(
            (lambda self: _SystemParametersInfo(nget)) if nget else None,
            (lambda self, x: _SystemParametersInfo(nset, x, flags)) if nset else None,
            None,
            doc)

    running = _property(win32con.SPI_GETSCREENSAVERRUNNING, None, 
                        "Boolean; running status. Read-only.")

    active = _property(win32con.SPI_GETSCREENSAVEACTIVE, win32con.SPI_SETSCREENSAVEACTIVE, 
                       "Boolean; active status (i.e. set up to launch).")

    secure = _property(win32con.SPI_GETSCREENSAVESECURE, win32con.SPI_SETSCREENSAVESECURE, 
                       "Boolean; secure status (i.e. requires psw on exit). Available on Vista+.")

    timeout = _property(win32con.SPI_GETSCREENSAVETIMEOUT, win32con.SPI_SETSCREENSAVETIMEOUT, 
                        "Integer; timeout in seconds.")

screensaver = _Screensaver()
