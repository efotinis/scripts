import os
import win32api
import win32con
import win32ui
import _winreg
import efRegistry
import efScriptInfo


def main():
    appsPath = 'HKCR\\Applications'

    badKeys = []
    for s in efRegistry.getRegSubkeys(appsPath):
        testApp(os.path.join(appsPath, s), badKeys)

    s = '\n'.join([t[0] + '\n\t' + t[1] + '\n' for t in badKeys])
    if s:
        s += '\n'
    s += '- ' * 40 + '\n'
    s += 'Invalid apps detected: %d\n' % len(badKeys)
    s += '\n'
    s += 'Hit Ctrl+C to copy results to clipboard.'
    
    icon = (win32con.MB_ICONEXCLAMATION if badKeys else
            win32con.MB_ICONINFORMATION)

    win32ui.MessageBox(s, efScriptInfo.getName(), icon)


def testApp(regPath, badKeys):
    # skip apps don't want to appear in 'Open With...'
    if tryRegRead(regPath, 'NoOpenWith') is not None:
        return

    shellPath = os.path.join(regPath, 'shell')
    try:
        verbs = efRegistry.getRegSubkeys(shellPath)
    except WindowsError:
        return

    for s in verbs:
        cmdPath = os.path.join(regPath, 'shell', s, 'command')
        testAppCmd(cmdPath, badKeys)


def testAppCmd(regPath, badKeys):
    data = tryRegRead(regPath, '');
    # skip invalid (non-string) data
    if not isinstance(data, basestring):
        return
    data = win32api.ExpandEnvironmentStrings(data)
    if not findExeFromCmd(data):
        badKeys += [(regPath, data)]


def tryRegRead(keyPath, value):
    """Return a value's data or None on error."""
    try:
        rk = 0
        rk = efRegistry.openKeyPath(keyPath)
        return _winreg.QueryValueEx(rk, value)[0]
    except (WindowsError, ValueError):
        return None
    finally:
        if rk:
            _winreg.CloseKey(rk)
        

def findExeFromCmd(s):
    if not s:
        return False

    if s == r'C:\PROGRA~1\MICROS~3\Office10\FRONTPG.EXE':
        pass

    # test for '"path" ...'
    if s.startswith('"'):
        i = s.find('"', 1)
        if i == -1:
            # no closing quotes
            return False
        return os.path.isfile(s[1:i])

    # test for 'RUNDLL32[.EXE] path,...'
    runDllPath = getRunDllPath(s)
    if runDllPath:
        return os.path.isfile(runDllPath)
    
    # test 'path ...'
    return heuristicPathScan(s)


def getRunDllPath(s):
    """Given 'X Y[,Z]', return 'Y' if 'X' is 'RUNDLL32[.EXE]', else None"""
    a = s.split(' ', 1)
    if len(a) != 2 or a[0].upper() not in ('RUNDLL32', 'RUNDLL32.EXE'):
        return None
    a = a[1].split(',', 1)
    return a[0];


def heuristicPathScan(s):
    """Test a command with a non-quoted first token."""

    # Since the Shell uses CreateProcess to launch the command,
    # this func duplicates CreateProcess's scan strategy (from the SDK).
    
    # check up to each space
    a = s.split(' ')
    for i in range(len(a)):
        path = ' '.join(a[:i+1])
        if heuristicPathScan2(path):
            return True

    return False


def heuristicPathScan2(s):
    global SCAN_DIRS
    
    # append '.exe' if there's no dir and no extension
    a = os.path.split(s)
    hasDir = bool(a[0])
    if not hasDir:
        a = os.path.splitext(a[1])
        if not a[1]:
            s += '.exe'

    if hasDir:
        return os.path.isfile(s)

    for dir in SCAN_DIRS:
        if os.path.isfile(os.path.join(dir, s)):
            return True

    return False        


def createProcessScanDirs():
    sysDir32 = win32api.GetSystemDirectory()
    winDir = win32api.GetWindowsDirectory()
    sysDir16 = os.path.join(winDir, 'System')
    pathDirs = os.environ['path'].split(';')
    # may contain duplicates, but it's no big deal
    return [sysDir32, sysDir16, winDir] + pathDirs


SCAN_DIRS = createProcessScanDirs()
main()
