"""SendTo menu extension to move Shell items up one directory level."""

import os
import sys
import argparse
import CommonTools
import win32api, win32file, win32con
import win32com.client
from win32com.shell import shell, shellcon

WshShell = win32com.client.Dispatch("WScript.Shell")


def isRunningInConsole():
    try:
        win32file.CreateFile(
            'CONOUT$', win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None, win32file.OPEN_EXISTING, 0, 0)
        return True
    except:
        return False


class ConsoleIO:
    def __init__(self):
        self.errwrite = sys.stderr.write
    def prn(self, s):
        print s
    def err(self, s):
        self.errwrite('ERROR: ' + s + '\n')
    def yesno(self, s):
        while True:
            response = raw_input(s + ' ([Y]es/[N]o)').strip().lower()
            if response == 'y':
                return True
            if response == 'n':
                return False


class WindowsIO:
    def __init__(self):
        self.msgbox = win32api.MessageBox
        self.scriptname = CommonTools.scriptname()
    def prn(self, s):
        self.msgbox(0, s, self.scriptname, 0)
    def err(self, s):
        self.msgbox(0, s, self.scriptname, win32con.MB_ICONERROR)
    def yesno(self, s):
        response = self.msgbox(0, s, self.scriptname,
                               win32con.MB_ICONQUESTION | win32con.MB_YESNO)
        return True if response == win32con.IDYES else False


IO = ConsoleIO() if isRunningInConsole() else WindowsIO()


##IO.err('you haven\'t answered my question yet!')
##x = IO.yesno('42?')
##IO.prn('you said "%s"' % ('Yes' if x else 'No'))


def getShortcutPaths():
    sendToDir = WshShell.SpecialFolders("SendTo")
    nbsp = ' ' #'\u00a0'
    # nbsp forces the 2nd shortcut after the other one in the SendTo menu
    # (its sorting seems buggy)
    return (os.path.join(sendToDir, "Parent.lnk"),
            os.path.join(sendToDir, "Parent" + nbsp + "& delete container.lnk"))


def doInstall():
    paths = getShortcutPaths()
    scriptpath = '"' + sys.argv[0] + '"'
    extraParams = (scriptpath, scriptpath + ' /d')
    descriptions = (
        'Moves items to parent directory.',
        'Moves items to parent directory and deletes their original directory.')
    # We can't just use "script.pyw" as the TargetPath, because then we can't
    # use the /d switch; everything after "script.pyw" is replaced with the
    # item paths.
    # However, when we use '"path_to_pythonw.exe" "script.pyw"', the /d
    # switch is preserved.
    ok = True
    for path, extra, descr in zip(paths, extraParams, descriptions):
        print path
        try:
            props = {
                'FullName': path,
                # TODO: un-hardcode this
                'TargetPath': r'"C:\Program Files\Python\pythonw.exe"',
                'Arguments': extra,
                'WorkingDirectory': '%USERPROFILE%',  # used to be the SENDTO dir
                'Description': descr,
                'IconLocation': r'D:\projects\test.ico'
            }
            createShortcut(props)
        except win32com.client.pywintypes.com_error:
            IO.err('could not create shortcut "%s"' % path)
            ok = False
    return ok
        

def doUninstall():
    ok = True
    for s in getShortcutPaths():
        try:
            os.unlink(s)
        except OSError:
            ok = False
    return ok


def createShortcut(props):
    '''
    Create a shortcut file using the specified properties.
    Valid properties:
        Arguments           program params
        Description         description
        FullName            shortcut path (required)
        Hotkey              hotkey combo (e.g. 'CTRL+SHIFT+F')
        IconLocation        icon path and optional index (e.g. 'notepad.exe, 0')
        RelativePath        relative path in case FullName is not absolute
        TargetPath          target path (must be valid, otherwise Save() fails)
        WindowStyle         1: normal, 3: maximized, 7: minimized
        WorkingDirectory    working dir
    '''
    lnk = WshShell.CreateShortcut(props['FullName'])
    # TODO: assign with something like 'lnk[p] = v'
    for p, v in props.iteritems():
        if p == 'FullName':           pass  # already used in CreateShortcut
        elif p == 'Arguments':        lnk.Arguments        = v
        elif p == 'Description':      lnk.Description      = v
        elif p == 'Hotkey':           lnk.Hotkey           = v
        elif p == 'IconLocation':     lnk.IconLocation     = v
        elif p == 'RelativePath':     lnk.RelativePath     = v
        elif p == 'TargetPath':       lnk.TargetPath       = v
        elif p == 'WindowStyle':      lnk.WindowStyle      = v
        elif p == 'WorkingDirectory': lnk.WorkingDirectory = v
    lnk.Save()                   


def doMove(opt, params):
    try:
        ok = True
        dirsToDelete = set()
        for s in params:
            if moveItemUp(s):
                dirsToDelete.add(os.path.dirname(s))
            else:
                ok = False
        if opt.delDirs:
            for s in dirsToDelete:
                err, anyAbort = shellDelete([s])
                if err:
                    ok = False
                    IO.err('could not delete "%s"; err:%d' % (s, err))
        return ok
    except StopIteration:
        return False


def moveItemUp(itemPath):
    srcDir = os.path.dirname(itemPath)
    dstDir = os.path.dirname(srcDir)

    # ignore items at root
    if (os.path.ismount(srcDir)):
        return False

    newPath = os.path.join(dstDir, os.path.basename(itemPath))
    err, anyAbort = shellMove([itemPath], [newPath])
    if err:
        prompt = 'could not move "%s"; continue?' % itemPath
        if IO.yesno(prompt):
            return False
        else:
            raise StopIteration
    return True


def shellMove(src, dst):
    '''Move a list of items to some new locations, using SHFileOperation.
    Return SHFileOperation's result.'''
    flags = shellcon.FOF_MULTIDESTFILES | shellcon.FOF_RENAMEONCOLLISION
    return shell.SHFileOperation((
        0,  # hwnd
        shellcon.FO_MOVE,
        '\0'.join(src),
        '\0'.join(dst),
        flags,
        None,
        None))


def shellDelete(items):
    '''Delete a list of items, using SHFileOperation.
    Return SHFileOperation's result.'''
    flags = shellcon.FOF_ALLOWUNDO
    return shell.SHFileOperation((
        0,  # hwnd
        shellcon.FO_DELETE,
        '\0'.join(items),
        None,
        flags,
        None,
        None))


##srcPaths = [
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\New Folder\cdfreaks reg.txt',
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\New Folder\cdfreaks post.txt',
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\New Folder\ShellExView']
##
##dstPaths = [
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\cdfreaks reg.txt',
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\cdfreaks post.txt',
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\ShellExView']
##
##flags = shellcon.FOF_MULTIDESTFILES | shellcon.FOF_RENAMEONCOLLISION
##
##op = (
##    0,  # hwnd
##    shellcon.FO_MOVE,
##    '\0'.join(srcPaths),
##    '\0'.join(dstPaths),
##    flags,
##    None,
##    None)
##
##shell.SHFileOperation(op)


##srcPaths = [
##    r'C:\Documents and Settings\Elias\Desktop\file_op_test\New Folder']
##
##flags = shellcon.FOF_ALLOWUNDO
##
##op = (
##    0,  # hwnd
##    shellcon.FO_DELETE,
##    '\0'.join(srcPaths),
##    None,
##    flags,
##    None,
##    None)
##
##print shell.SHFileOperation(op)


def parse_args():
    ap = argparse.ArgumentParser(
        description='move items one directory up and optionally delete original parent'
        add_help=False)
    group = ap.add_mutually_exclusive_group(required=True)
    add = group.add_argument
    add('-i', dest='install', action='store_true',
        help='add SendTo menu shortcuts'),
    add('-u', dest='uninstall', action='store_true',
        help='remove SendTo menu shortcuts'),
    ap.add_argument('-d', dest='delDirs', action='store_true',
        help='Delete containers of affected files, along with any other files '
        'they contain. Deleted items go to the Recycle Bin.'),
    add('items', nargs='*',
        'the items to move; items located on a root dir are ignored')
    args = ap.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    try:
        #win32api.Sleep(1000)
        #IO.prn(str(sys.argv[1:]))
        if opt.install:
            res = doInstall()
        elif opt.uninstall:
            res = doUninstall()
        else:
            res = doMove(opt, params)
        if not res:
            sys.exit(1)
    except Exception, x:
        IO.err('unexpected error: ' + str(x))
