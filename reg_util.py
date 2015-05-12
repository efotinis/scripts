"""High-level Registry utilities.

Note that the original module name "regutil" was changed because
it conflicts with a pythonwin module 
(C:\Python27\Lib\site-packages\win32\lib\regutil.py)
"""

import contextlib
import itertools

try:
    import _winreg as winreg
    from _winreg import KEY_READ, KEY_WRITE, REG_SZ
except ImportError:
    import winreg
    from winreg import KEY_READ, KEY_WRITE, REG_SZ
from winerror import ERROR_FILE_NOT_FOUND

# better leave it to the caller to import needed consts themselves
### copy _winreg's numeric attributes so callers need not
### import it to use the KEY_*, REG_* and HKEY_* constants
### (essentially a shorthand for "from _winreg import ...")
##for name, obj in vars(_winreg).items():
##    if isinstance(obj, (int, long)):
##        vars()[name] = obj


@contextlib.contextmanager
def open_key(parent, sub, res=0, sam=KEY_READ):
    """Context manager that automatically closes the returned key."""
    key = winreg.OpenKey(parent, sub, res, sam)
    try:
        yield key
    finally:
        key.Close()


@contextlib.contextmanager
def create_key(parent, sub, res=0, sam=KEY_WRITE):
    """Context manager that automatically closes the returned key."""
    key = winreg.CreateKeyEx(parent, sub, res, sam)
    try:
        yield key
    finally:
        key.Close()


def get_value(key, name, default=(None, None)):
    """Get value data/type; use default if missing."""
    try:
        return winreg.QueryValueEx(key, name)
    except WindowsError as x:
        if x.winerror == ERROR_FILE_NOT_FOUND:
            return default
        raise


def set_value(key, name, x, type_):
    try:
        winreg.SetValueEx(key, name, 0, type_, x)
        return True
    except WindowsError:
        return False


def delete_value(key, name):
    try:
        winreg.DeleteValue(key, name)
        return True
    except WindowsError:
        return False


def get_value_data(key, name, type_, default=None):
    """Get value data; use default if missing or of different type."""
    try:
        data, valtype = winreg.QueryValueEx(key, name)
        return data if valtype == type_ else default
    except WindowsError as x:
        if x.winerror == ERROR_FILE_NOT_FOUND:
            return default
        raise


# TODO: replace 'end' with 'count'

def get_list(key, basename, type_=REG_SZ, start=0, end=None):
    """Get list of (index,data) of consecutive 'basenameN' values.

    Values not of type_ are ignored. If end is None, the first missing
    value stops enumeration, otherwise missing values are ignored. The
    ending index is not included.
    """
    if end is not None and end <= start:
        raise ValueError('end must be >start or None')
    ret = []
    for i in itertools.count(start):
        if end is not None and i >= end:
            break
        name = basename + str(i)
        data, curtype = get_value(key, name)
        if data is None:
            if end is None:
                break
            else:
                continue
        if curtype != type_:
            continue
        ret.append((i, data))
    return ret


def set_list(key, basename, type_, data, start=0, end=None):
    """Set homogeneous list (data) of consecutive 'basenameN' values.

    If end is None, the value after the last one is deleted, otherwise
    all values up to (but not including) the ending index are deleted.

    Returns True if everything succeeded.
    """
    if end is not None and end <= start:
        raise ValueError('end must be >start or None')
    if end is not None and end - start > len(data):
        raise ValueError('too many items specified')

    error = False

    i = start
    for x in data:
        name = basename + str(i)
        if set_value(key, name, x, type_):
            i += 1
        else:
            error = True

    if end is None:
        # unbound list; clear one
        name = basename + str(i)
        if not delete_value(key, name):
            error = True
    else:
        # bound list; clear all
        while i < end:
            name = basename + str(i)
            if not delete_value(key, name):
                error = True
            i += 1

    return not error
