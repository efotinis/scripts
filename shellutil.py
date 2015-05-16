"""Windows Shell utilities.

TODO: replace with winshell by Tim Golden.

tags: shell
compat: 2.7+, 3.3+
platform: Windows
"""

import os
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import win32gui
import win32com.client
from win32com.shell import shell, shellcon
import six


# TODO: maybe provide a KnownFolders (similar to special folders),
#       based on SHGetKnownFolderPath(), since it gives access to more
#       folders than SHGetFolderPath().


# TODO: things to get from elsewhere:
#
#   D:\docs\data\desktop dump\2010-0507\places bar customizing\shellcomdlg.py
#
#   D:\docs\python\IKnownFolderManager.py  (?)
#
#   D:\docs\python\shell assoc change notify.py
#   (handy when manually editing the Registry, for example)


def get_open_explorer_directories():
    """Generate the (HWND,path) of open Windows Explorer folder windows.

    Only filesystem folders are returned.
    """

    shell_app = win32com.client.Dispatch('Shell.Application')
    shell_wnds = shell_app.Windows()  # ShellWindows object

    # enumerate InternetExplorer objects in ShellWindows collection
    for ie in shell_app.Windows():
        hwnd = int(ie.HWND)
        cls = win32gui.GetClassName(hwnd)
        # we're only interested in Windows Explorer windows (enum includes IE)
        if cls.lower() == 'CabinetWClass'.lower():
            url = urlparse.urlsplit(ie.LocationURL)
            if url.scheme == 'file':
                # convert 'file:///...' to Windows path
                url = os.path.normpath(urlparse.unquote(url.path.lstrip('/')))
                yield hwnd, url


def create_shortcut(path, target=None, args=None, cwd=None, hotkey=None,
                    wstyle=None, comment=None, icon=None, update=False):
    """Create a Windows shortcut (.LNK).

    path        shortcut file path
    target      target path
    args        arguments string
    cwd         "Start in" directory
    hotkey      hotkey string: "[Alt+][Ctrl+][Shift+][Ext+][key]";
                (case insesitive; no whitespace allowed)
    wstyle      initial window state: '' (normal; default), 'min', 'max'
    comment     description
    icon        icon location: "icon_container[, index]".
    update      update existing shortcut (if false, always create new);
                should be false when creating a new shortcut, since only
                explicitly set parameters get assigned
    """

    wshshell = win32com.client.Dispatch("WScript.Shell")  # WshShell object

    # CreateShortCut() always loads an existing shortcut implicitly;
    # an alternative would be to create a ShellLink object,
    # which can be controlled explicitly via IPersistFile:
    #   sl = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, 
    #       pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
    #   pf = sl.QueryInterface(pythoncom.IID_IPersistFile)
    #   pf.Load(...)  # optional

    if not update:
        try:
            os.unlink(path)
        except OSError:
            pass
    shortcut = wshshell.CreateShortCut(path)  # WshShortcut object

    if target is not None:
        shortcut.TargetPath = target
    if args is not None:
        shortcut.Arguments = args
    if cwd is not None:
        shortcut.WorkingDirectory = cwd
    if hotkey is not None:
        shortcut.Hotkey = hotkey
    if wstyle is not None:
        shortcut.WindowStyle = {'':1, 'max':3, 'min':7}[wstyle]
    if comment is not None:
        shortcut.Description = comment
    # an uninitialized icon will be automagically set to a reasonable default;
    # only works with newly created objects (they return ' ,0' for the icon,
    # but note that setting this special value manually doesn't work)
    if icon is not None:
        shortcut.IconLocation = icon

    shortcut.save()


def load_shortcut(path):
    """Load a Windows shortcut (.LNK) as a dict.clear

    The returned items can be used as params to create_shortcut().
    """
    wshshell = win32com.client.Dispatch("WScript.Shell")  # WshShell object
    shortcut = wshshell.CreateShortCut(path)  # WshShortcut object
    return {'target':shortcut.TargetPath, 'args':shortcut.Arguments,
            'cwd':shortcut.WorkingDirectory, 'hotkey':shortcut.Hotkey,
            'wstyle':{1:'', 3:'max', 7:'min'}[shortcut.WindowStyle],
            'comment':shortcut.Description, 'icon':shortcut.IconLocation,}


class SpecialFolders(object):
    """Get the paths of special folders via attribute access.

    Supports all CSIDL_* folders, available as attributes named from the part
    after the 'CSIDL_' prefix, ignoring case (e.g. 'desktop' for CSIDL_DESKTOP,
    'common_AppData' for CSIDL_COMMON_APPDATA).

    Example:
    >>> SpecialFolders().desktop
    u'C:\\Users\\Elias\\Desktop'

    Note that virtual folders (CSIDL_BITBUCKET, CSIDL_COMPUTERSNEARME,
    CSIDL_CONNECTIONS, CSIDL_CONTROLS, CSIDL_DRIVES, CSIDL_INTERNET,
    CSIDL_NETWORK, CSIDL_PRINTERS) will raise COM error -2147467259
    (0x80004005: Unspecified error)

    Also, some folders (e.g. CSIDL_COMMON_OEM_LINKS, CSIDL_RESOURCES_LOCALIZED)
    may raise COM error -2147024894 (0x80070002: The system cannot find the
    file specified)
    """
    
    SHGFP_TYPE_CURRENT = 0  # not in shellcon
    ATTRIBS = {s[6:].lower():getattr(shellcon, s)
               for s in dir(shellcon) if s.startswith('CSIDL_')}
    # fix shellcon bug (probably PSDK typo)
    ATTRIBS['mydocuments'] = ATTRIBS['personal']

    def __getattr__(self, name):
        try:
            return shell.SHGetFolderPath(0, self.ATTRIBS[name.lower()], None,
                                         self.SHGFP_TYPE_CURRENT)
        except KeyError:
            raise AttributeError('unknown folder "%s"' % name)

    def __setattr__(self, name, value):
        raise AttributeError('attributes are read-only')

    def __dir__(self):
        return self.ATTRIBS.keys()


SpecialFolders = SpecialFolders()


def delete_items(paths):
    wnd = 0
    op = shellcon.FO_DELETE
    src = '\0'.join(paths)
    dst = None
    flags = (shellcon.FOF_SILENT | shellcon.FOF_NOCONFIRMATION |
             shellcon.FOF_NOERRORUI)
    failed, any_aborted = shell.SHFileOperation((wnd, op, src, dst, flags))
    return failed, any_aborted


def recycle_items(paths):
    wnd = 0
    op = shellcon.FO_DELETE
    src = '\0'.join(paths)
    dst = None
    flags = (shellcon.FOF_SILENT | shellcon.FOF_NOCONFIRMATION |
             shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOERRORUI)
    failed, any_aborted = shell.SHFileOperation((wnd, op, src, dst, flags))
    return failed, any_aborted


def move_items(paths, dest):
    wnd = 0
    op = shellcon.FO_MOVE
    src = '\0'.join(paths)
    flags = (shellcon.FOF_SILENT | shellcon.FOF_NOCONFIRMATION |
             shellcon.FOF_NOERRORUI | shellcon.FOF_NOCONFIRMMKDIR)
    if isinstance(dest, six.string_types):
        dst = dest
    else:
        dst = '\0'.join(dest)
        flags |= shellcon.FOF_MULTIDESTFILES
    failed, any_aborted = shell.SHFileOperation((wnd, op, src, dst, flags))
    return failed, any_aborted
