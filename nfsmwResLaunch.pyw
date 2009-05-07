"""Automatically start NFSMWRes, launch NFSMW, and close NFSMWRes.

MFSMW must be installed.
NFSMWRes must be in the game dir and properly configured.
"""

import os
import subprocess
import win32api
import win32gui
import win32con
import _winreg

def getGameDir():
    """Read game dir from registry."""
    def tryOpenLmKey(path):
        try:
            return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)
        except WindowsError:
            return None
    key = (tryOpenLmKey(r'SOFTWARE\Wow6432Node\EA GAMES\Need for Speed Most Wanted')
           or tryOpenLmKey(r'SOFTWARE\EA GAMES\Need for Speed Most Wanted'))
    if key:
        data, type = _winreg.QueryValueEx(key, 'Install Dir')
        if type == _winreg.REG_SZ:
            return data
    raise RuntimeError('could not read NFSMW install dir from registry')

def waitFindWindow(cls, title, msec=100, times=10):
    """FindWindow with retry."""
    for i in range(times):
        try:
            return win32gui.FindWindow(cls, title)
        except win32gui.error:
            pass
        win32api.Sleep(msec)
    else:
        raise RuntimeError('could not find window')

try:
    exe = os.path.join(getGameDir(), 'nfsmwres.exe')
    subprocess.Popen(exe, cwd=r'E:\games\Need for Speed Most Wanted')
    wnd = waitFindWindow('ThunderRT6FormDC', 'NFSMWRes')
    btn = win32gui.FindWindowEx(wnd, 0, 'ThunderRT6CommandButton', 'Launch')
    win32api.SendMessage(btn, win32con.BM_CLICK)
    win32api.Sleep(1000)  # give the trainer some time to fix the code
    win32api.SendMessage(wnd, win32con.WM_CLOSE)
except Exception as x:
    win32api.MessageBox(0, str(x), 'Error', win32con.MB_ICONERROR)
