"""High-level Registry utilities.

Note that the original module name "regutil" was changed because
it conflicts with a pythonwin module 
(C:\Python27\Lib\site-packages\win32\lib\regutil.py)
"""

import contextlib
import itertools
import _winreg

from winerror import ERROR_FILE_NOT_FOUND
from _winreg import KEY_READ, REG_SZ

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
    key = _winreg.OpenKey(parent, sub, res, sam)
    try:
        yield key
    finally:
        key.Close()


def get_value(key, name, default=(None, None)):
    """Get value data/type; use default if missing."""
    try:
        return _winreg.QueryValueEx(key, name)
    except WindowsError as x:
        if x.winerror == ERROR_FILE_NOT_FOUND:
            return default
        raise


def get_value_data(key, name, type_, default=None):
    """Get value data; use default if missing or of different type."""
    try:
        data, valtype = _winreg.QueryValueEx(key, name)
        return data if valtype == type_ else default
    except WindowsError as x:
        if x.winerror == ERROR_FILE_NOT_FOUND:
            return default
        raise


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
