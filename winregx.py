#!python3
"""Registry utilities and a simple wrapper class of winreg key functions."""

import datetime
import itertools
import winreg

from errno import EINVAL


ROOTNAMES = {
    'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT, 
    'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER, 
    'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE, 
    'HKEY_USERS': winreg.HKEY_USERS, 
    'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG, 
    'HKEY_DYN_DATA': winreg.HKEY_DYN_DATA, 
    'HKEY_PERFORMANCE_DATA': winreg.HKEY_PERFORMANCE_DATA, 
    'HKCR': winreg.HKEY_CLASSES_ROOT, 
    'HKCU': winreg.HKEY_CURRENT_USER, 
    'HKLM': winreg.HKEY_LOCAL_MACHINE, 
    'HKU': winreg.HKEY_USERS, 
    'HKCC': winreg.HKEY_CURRENT_CONFIG, 
    'HKDD': winreg.HKEY_DYN_DATA, 
    'HKPD': winreg.HKEY_PERFORMANCE_DATA, 
}


def subkeys(key):
    """Generate subkey names."""
    for i in itertools.count():
        try:
            yield winreg.EnumKey(key, i)
        except OSError as x:
            if x.errno == EINVAL:
                return
            raise


def values(key):
    """Generate (name,data,type) of values."""
    for i in itertools.count():
        try:
            yield winreg.EnumValue(key, i)
        except OSError as x:
            if x.errno == EINVAL:
                return
            raise


def valuenames(key):
    """Generate value names."""
    # TODO: this could be optimized
    for name, data, type_ in values(key):
        yield name


def getvalue(key, name, default=None):
    """Get value data/type or default if non-None."""
    try:
        return winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        if default is None:
            raise
        return default


def _split(root, path):
    """Replace root with first path component if root is None."""
    if not root:
        head, sep, tail = path.partition('\\')
        root = ROOTNAMES[head.upper()]
        path = tail
    return int(root), path


def _filetime_to_datetime(ft):
    """Convert a Windows FILETIME to a Python datetime."""
    return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=ft / 10)


def open(key, sub, access=winreg.KEY_READ):
    return Key(winreg.OpenKeyEx(*_split(key, sub), reserved=0, access=access))


def create(key, sub, access=winreg.KEY_WRITE):
    return Key(winreg.CreateKeyEx(*_split(key, sub), reserved=0, access=access))


def connect(machine, key):
    return Key(winreg.ConnectRegistry(machine, key))


class Key(object):

    def __init__(self, key):
        if not isinstance(key, winreg.HKEYType):
            raise TypeError('key is not a PyHKEY')
        self.key = key

    def close(self):
        if self.key:
            winreg.CloseKey(self.key)

    def delete(self, sub, access=0):
        if access:
            winreg.DeleteKeyEx(self.key, sub, access, 0)
        else:
            winreg.DeleteKey(self.key, sub)

    def subkeys(self):
        return subkeys(self.key)

    def values(self):
        return values(self.key)

    def valuenames(self):
        return valuenames(self.key)

    def flush(self):
        winreg.FlushKey(self.key)

    def save(self, path):
        winreg.SaveKey(self.key, path)

    def load(self, sub, path):
        winreg.LoadKey(self.key, sub, path)

    def info(self):
        keys, values, modified = winreg.QueryInfoKey(self.key)
        return keys, values, _filetime_to_datetime(modified)

    def getdefvalue(self, sub):
        return winreg.QueryValue(self.key, sub)
    
    def setdefvalue(self, sub, value):
        winreg.SetValue(self.key, sub, winreg.REG_SZ, value)
        
    def getvalue(self, name, default=None):
        return getvalue(self.key, name, default)

    def setvalue(self, name, value_type):
        winreg.SetValueEx(self.key, name, 0, value_type[1], value_type[0])
        
    def delvalue(self, name):
        winreg.DeleteValue(self.key, name)

    def __bool__(self):
        return bool(self.key)

    def __int__(self):
        return int(self.key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


##winreg.EnableReflectionKey
##winreg.DisableReflectionKey
##winreg.QueryReflectionKey
