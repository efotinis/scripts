"""Automatically launch custom res tools for various Need For Speed games.

The games and the tools must be properly installed and configured.
This means that the res tools must be in the game dir and the resolution
must have been already specified in them.
"""

import os
import sys
import subprocess
import win32api
import win32gui
import win32con
import _winreg


# usage: regpath64, regpath32, toolfile, toolcaption = SETTINGS[gameid]
SETTINGS = {
    'mostwanted': (
        r'SOFTWARE\Wow6432Node\EA GAMES\Need for Speed Most Wanted',
        r'SOFTWARE\EA GAMES\Need for Speed Most Wanted',
        'nfsmwres.exe',
        'nfsmwres'),
    'carbon': (
        r'SOFTWARE\Wow6432Node\Electronic Arts\Need for Speed Carbon',
        r'SOFTWARE\Electronic Arts\Need for Speed Carbon',
        'nfscres.exe',
        'nfscres')}
        

def getgamedir(path64, path32):
    """Read game dir from registry."""
    def tryOpenLmKey(path):
        try:
            return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path)
        except WindowsError:
            return None
    key = (tryOpenLmKey(path64) or tryOpenLmKey(path32))
    if key:
        data, type = _winreg.QueryValueEx(key, 'Install Dir')
        if type == _winreg.REG_SZ and data:
            return data
    raise RuntimeError('could not read install dir from registry')


def waitfindwindow(cls, title, msec=100, times=10):
    """FindWindow with retry."""
    for i in range(times):
        try:
            return win32gui.FindWindow(cls, title)
        except win32gui.error:
            pass
        win32api.Sleep(msec)
    else:
        raise RuntimeError('could not find window')


if __name__ == '__main__':
    try:
        try:
            (gameid,) = sys.argv[1:]
        except ValueError:
            raise ValueError('exactly one game-id parameter must be specified')
        try:
            REGPATH64, REGPATH32, TOOLFILE, TOOLCAPTION = SETTINGS[gameid]
        except KeyError:
            raise ValueError('invalid game-id; must be one of: ' + ', '.join(SETTINGS.keys()))
        
        gamedir = getgamedir(REGPATH64, REGPATH32)
        subprocess.Popen(os.path.join(gamedir, TOOLFILE), cwd=gamedir)
        wnd = waitfindwindow('ThunderRT6FormDC', TOOLCAPTION)

        if gameid == 'carbon':
            # the version does not persist, so we must select it manually;
            # there are 2 "v1.3" controls, the first one is hidden
            ver_radio = win32gui.FindWindowEx(wnd, 0, 'ThunderRT6OptionButton', 'v1.3')
            ver_radio = win32gui.FindWindowEx(wnd, ver_radio, 'ThunderRT6OptionButton', 'v1.3')
            win32api.SendMessage(ver_radio, win32con.BM_CLICK)
        
        btn = win32gui.FindWindowEx(wnd, 0, 'ThunderRT6CommandButton', 'Launch')
        win32api.SendMessage(btn, win32con.BM_CLICK)

        win32api.Sleep(5000)  # give the trainer some time to fix the code
        win32api.SendMessage(wnd, win32con.WM_CLOSE)

    except Exception as x:
        win32api.MessageBox(0, str(x), 'Error', win32con.MB_ICONERROR)
