import os
import _winreg
import win32con
import winerror
import ctypes

from ctypes.wintypes import DWORD, HKEY, LPCWSTR, LPVOID


SHDeleteKey = None
RegCreateKeyEx = None


regRootLongStrings = {
    'HKEY_CLASSES_ROOT':     win32con.HKEY_CLASSES_ROOT,
    'HKEY_CURRENT_USER':     win32con.HKEY_CURRENT_USER,
    'HKEY_LOCAL_MACHINE':    win32con.HKEY_LOCAL_MACHINE,
    'HKEY_USERS':            win32con.HKEY_USERS,
    'HKEY_CURRENT_CONFIG':   win32con.HKEY_CURRENT_CONFIG,
    'HKEY_DYN_DATA':         win32con.HKEY_DYN_DATA,
    'HKEY_PERFORMANCE_DATA': win32con.HKEY_PERFORMANCE_DATA,
    'HKEY_PERFORMANCE_TEXT': win32con.HKEY_PERFORMANCE_TEXT,
    'HKEY_PERFORMANCE_NLSTEXT': win32con.HKEY_PERFORMANCE_NLSTEXT}


regRootShortStrings = {
    'HKCR': win32con.HKEY_CLASSES_ROOT,
    'HKCU': win32con.HKEY_CURRENT_USER,
    'HKLM': win32con.HKEY_LOCAL_MACHINE,
    'HKU':  win32con.HKEY_USERS,
    'HKCC': win32con.HKEY_CURRENT_CONFIG,
    'HKDD': win32con.HKEY_DYN_DATA,
    'HKPD': win32con.HKEY_PERFORMANCE_DATA,
    'HKPT': win32con.HKEY_PERFORMANCE_TEXT,
    'HKPN': win32con.HKEY_PERFORMANCE_NLSTEXT}


def get_root(s):
    """Map a long/short root string to a predefined key (may raise KeyError)."""
    if s.startswith('HKEY_'):
        return regRootLongStrings[s]
    else:
        return regRootShortStrings[s]


def openKeyPath(path, res=0, sam=win32con.KEY_READ):
    """Open a reg key using a complete string path."""
    # split the first component (root) from the rest
    a = path.replace('\\', '/', 1).split('/', 1)
    # append a nul path if none was specified
    if len(a) == 1:
        a.append('')
    # convert root string to predefined handle
    s = a[0].upper()
    if s in regRootLongStrings:
        a[0] = regRootLongStrings[s]
    elif s in regRootShortStrings:
        a[0] = regRootShortStrings[s]
    else:
        raise ValueError('Invalid registry root key.')
    return _winreg.OpenKey(a[0], a[1], res, sam)


def _getRegHelper(key, subkeyPath, enumFunc):
    if isinstance(key, basestring):
        rk = openKeyPath(os.path.join(key, subkeyPath) if subkeyPath else key)
    else:
        rk = _winreg.OpenKey(key, subkeyPath)
    
    try:
        a = []
        i = 0
        while True:
            a += [enumFunc(rk, i)]
            i += 1
    except WindowsError, x:
        if x.winerror != winerror.ERROR_NO_MORE_ITEMS:
            raise
    finally:
        _winreg.CloseKey(rk)

    return a


def getRegSubkeys(key, subkeyPath=''):
    """Return the names of all subkeys names of key+subkeyPath."""
    return _getRegHelper(key, subkeyPath,
                         lambda rk, i: _winreg.EnumKey(rk, i))


def getRegValueNames(key, subkeyPath=''):
    """Return the names of all value names of key+subkeyPath."""
    return _getRegHelper(key, subkeyPath,
                         lambda rk, i: _winreg.EnumValue(rk, i)[0])


def getRegValues(key, subkeyPath=''):
    """Return the names of all values of key+subkeyPath."""
    return _getRegHelper(key, subkeyPath,
                         lambda rk, i: _winreg.EnumValue(rk, i))


def exportRegKey(keypath, file):
    """Export a registry key using REG.EXE.

    Root abbreviations like HKLM and HKCU are allowed.
    If 'file' already exists, the operation fails.
    Returns boolean success.
    """
    cmd = 'reg.exe export "%s" "%s">nul 2>&1' % (keypath, file)
    return os.system(cmd) == 0


def regKeyExists(keypath):
    """Check existance of a registry key.

    Root abbreviations like HKLM and HKCU are allowed.
    """
    try:
        _winreg.CloseKey(openKeyPath(keypath))
        return True
    except WindowsError, x:
        if x.errno != winerror.ERROR_FILE_NOT_FOUND:
            raise
    return False


def nukeKey(key, sub=''):
    """Delete a key recursively. 'key' can be a string or regkey object."""
    global SHDeleteKey
    if not SHDeleteKey:
        SHDeleteKey = ctypes.windll.shlwapi.SHDeleteKeyW  # 4.71+
        SHDeleteKey.restype = DWORD
        SHDeleteKey.argtypes = [HKEY, LPCWSTR]
    if isinstance(key, basestring):
        root, sub = os.path.normpath(os.path.join(key, sub)).split('\\', 1)
        key = get_root(root)
    err = SHDeleteKey(key, sub)
    if err:
        raise WindowsError(err)


def open_key(key, sub=None, options=0, sam=_winreg.KEY_READ):
    ret = Key()
    ret.open(key, sub, options, sam)
    return ret


def create_key(key, sub, res=0, cls=None, options=0, sam=_winreg.KEY_ALL_ACCESS, security=None):
    ret = Key()
    ret.create(key, sub, res, cls, options, sam, security)
    return ret


class Key:

    def __init__(self):
        self.key = None

    def __del__(self):
        if self.is_open():
            self.close()

    def open(self, key, sub=None, options=0, sam=_winreg.KEY_READ):
        self.key = _winreg.OpenKey(key, sub, options, sam)

##    def create(self, key, sub, res=0, cls=None, options=0,
##               sam=_winreg.KEY_ALL_ACCESS, security=None):
##        if not RegCreateKeyEx:
##            load_RegCreateKeyEx()
####        raise Exception('use ctypes to access CreateKeyEx')
####        self.key = _winreg.CreateKey(self.key, sub, options, sam)
##        h = HKEY(0)
##        dsp = DWORD(0)
##        err = RegCreateKeyEx(key, sub, res, cls, options, sam,
##                             security, ctypes.byref(h), ctypes.byref(dsp))
##        if err:
##            raise WindowsError(err)
##        self.key.handle = h.value
##        self.disposition = dsp
    def create(self, key, sub):
        self.key = _winreg.CreateKey(key, sub)

    def is_open(self):
        return self.key and self.key.handle

    def close(self):
        _winreg.CloseKey(self.key)

    def delete(self, sub=''):
        _winreg.DeleteKey(self.key, sub)

    def flush(self):
        _winreg.FlushKey(self.key)

##    def subkeys(self):
##        return Subkeys(self.key)
##
##    def values(self):
##        return Values(self.key)

    def __getattr__(self, s):
        if s == 'subkeys':
            return Subkeys(self.key)
        elif s == 'values':
            return Values(self.key)
##        elif s == 'valuenames':
##            return ValueNames(self.key)
        else:
            raise AttributeError

    def info(self):
        return _winreg.QueryInfoKey(self.key)


class Subkeys:

    def __init__(self, key):
        self.key = key

    def __len__(self):
        return _winreg.QueryInfoKey(self.key)[0]

    def __getitem__(self, index):
        return _winreg.EnumKey(self.key, index)

    def __iter__(self):
        return _Iter(self)


class Values:

    def __init__(self, key):
        self.key = key

    def __len__(self):
        return _winreg.QueryInfoKey(self.key)[1]

    def __getitem__(self, index_or_name):
        if isinstance(index_or_name, basestring):
            return _winreg.QueryValueEx(self.key, index_or_name)
        else:
            return _winreg.EnumValue(self.key, index_or_name)

    def __setitem__(self, name, data_and_type):
        _winreg.SetValueEx(self.key, name, 0, data_and_type[1], data_and_type[0])

    def __delitem__(self, name):
        _winreg.DeleteValue(self.key, name)

    def __iter__(self):
##        return _Iter(self, operator.itemgetter(0))
        return _Iter(self)

##    def full_iter(self):
##        return _Iter(self)

##    def delete(self, name):
##        _winreg.DeleteValue(self.key, name)


class _Iter:

    def __init__(self, container, data_selector=None):
        self.container = container
        self.cur_index = 0
        self.data_selector = data_selector

    def __iter__(self):
        return self

    def next(self):
        try:
            ret = self.container[self.cur_index]
            self.cur_index += 1
            return ret if not self.data_selector else self.data_selector(ret)
        except EnvironmentError:
            raise StopIteration


##    RegQueryMultipleValues Retrieves the type and data for a list of value names associated with an open registry key. 
##
##    RegReplaceKey Replaces the file backing a registry key and all its subkeys with another file. 
##    RegNotifyChangeKeyValue Notifies the caller about changes to the attributes or contents of a specified registry key. 
##    RegOpenCurrentUser Retrieves a handle to the HKEY_CURRENT_USER key for the user the current thread is impersonating. 
##    RegOpenUserClassesRoot Retrieves a handle to the HKEY_CLASSES_ROOT key for the specified user. 
##    RegOverridePredefKey Maps a predefined registry key to a specified registry key. 
##
##    RegUnLoadKey Unloads the specified registry key and its subkeys from the registry. 
##    RegRestoreKey Reads the registry information in a specified file and copies it over the specified key. 
##    RegLoadKey Creates a subkey under HKEY_USERS or HKEY_LOCAL_MACHINE and stores registration information from a specified file into that subkey. 
##    RegSaveKey Saves the specified key and all of its subkeys and values to a new file. 
##
##    RegConnectRegistry Establishes a connection to a predefined registry handle on another computer. 
##    RegDisablePredefinedCache Disables the predefined registry handle table of HKEY_CURRENT_USER for the specified process. 


##def load_RegCreateKeyEx():
##    global RegCreateKeyEx
##    try:
##        RegCreateKeyEx = ctypes.windll.advapi32.RegCreateKeyExW
##        wide = True
##    except AttributeError:
##        RegCreateKeyEx = ctypes.windll.advapi32.RegCreateKeyExA
##        wide = False
##    LONG = ctypes.c_long
##    HKEY = ctypes.c_void_p
##    LPTSTR = ctypes.c_wchar_p if wide else ctypes.c_char_p
##    LPCTSTR = LPTSTR
##    DWORD = ctypes.c_ulong
##    REGSAM = DWORD
##    LPSECURITY_ATTRIBUTES = ctypes.c_void_p
##    PHKEY = ctypes.POINTER(HKEY)
##    LPDWORD = ctypes.POINTER(DWORD)
##    RegCreateKeyEx.restype = LONG
##    RegCreateKeyEx.argtypes = [HKEY, LPCTSTR, DWORD, LPTSTR, DWORD, REGSAM,
##                               LPSECURITY_ATTRIBUTES, PHKEY, LPDWORD]


if __name__ == '__main__':
    k = open_key(_winreg.HKEY_CURRENT_USER, r'software\elias fotinis')
##    for s in k.subkeys():
##        print s
    k.open(k.key, 'deskpins')

