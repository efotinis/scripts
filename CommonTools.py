"""Common script utilities."""

import os
import sys
import contextlib
import math
import win32console
import WinTime

shell = shellcon = None  # delay load


# When STD_OUTPUT_HANDLE is not available (e.g. in PythonWin)
# GetStdHandle's behavior varies:
# - in Python 2.5 GetStdHandle succeeds but the returned handle is unusable
#   (so we just grab the handle and handle failure later during output)
# - in Python 2.6 GetStdHandle fails immediatelly,
#   so we need a try block
try:
    STDOUT = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
except win32console.error:
    STDOUT = None


class InFile:
    """Input file or STDIN."""

    def __init__(self, path=''):
        'Open input file or STDIN if path is "".'
        self.f = file(path) if path else sys.stdin

    def __iter__(self):
        return self

    def next(self):
        s = self.f.readline()
        if not s:
            raise StopIteration
        return s

    def close(self):
        if self.f is not sys.stdin:
            self.f.close()

    def readlines(self):
        return self.f.readlines()


class OutFile:
    """Output file or STDOUT."""

    def __init__(self, path=''):
        'Open output file or STDOUT if path is "".'
        self.f = file(path, 'w') if path else sys.stdout

    def close(self):
        if self.f is not sys.stdout:
            self.f.close()

    def write(self, s):
        self.f.write(s)


def scriptname():
    """Current script name, sans dir path and extension."""
    return os.path.splitext(os.path.basename(sys.argv[0]))[0]


def errln(s):
    """Print a message to STDERR, along with current script's name."""
    sys.stderr.write('ERROR: [%s] %s\n' % (scriptname(), s))


def uprint(s):
    """Print a unicode string followed by a newline.

    Useful for printing Unicode strings in the Windows console.
    """
    try:
        STDOUT.WriteConsole(s + '\n')
    except:
        print s


def splitunits(n, units):
    """Split a number to a tuple of units.

    The number must be non-negative and the units integers > 0.
    The fractional part (if any) goes to the lowest unit.

    # split 125sec to 2min:5sec
    >>> splitunits(125, (60,))
    (5, 2)
    
    # split 123456.7sec to 1days:10hrs:17min:36.7sec
    >>> splitunits(123456.7, (60,60,24))
    (36.7, 17, 10, 1)
    """
    if n < 0:
        raise ValueError('splitunits() number must be >= 0')
    ret = []
    for u in units:
        if int(u) != u or u <= 0:
            raise ValueError('splitunits() units must be ints > 0')
        ret += [n % u]
        n //= u
    ret.append(n)
    return tuple(ret)


def loadShell():
    global shell, shellcon 
    if not shell:
        from win32com.shell import shell, shellcon


def getDesktop():
    """Current user's desktop directory."""
    loadShell()
    SHGFP_TYPE_CURRENT = 0  # missing from shellcon
    return shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, None,
                                 SHGFP_TYPE_CURRENT)


def gotoDesktop():
    """Change working directory to current user's desktop."""
    os.chdir(getDesktop())


def prettysize(n, iec=False):
    """Convert size to string with 3 significant digits and unit.
    Negative sizes get a '-' prefix. iec==True inserts an 'i'."""
    n = int(n)
    if n < 0:
        return '-' + prettysize(-n)
    elif n == 1:
        return '1 byte'
    elif n < 1000:
        return '%d bytes' % n
    for unit in 'KMGTPEZY':
        n /= 1024.0
        if n < 1000:
            break
    else:
        # ran out of units; revert to last one
        n *= 1024.0
    if n < 999.5:
        s = '%.2f' % n  # has at least 3 digits
        t = ''
        digits = 0
        i = 0
        while digits < 3:
            t += s[i]
            if s[i].isdigit():
                digits += 1
            i += 1
        t = t.rstrip('.')
        return '%s %c%sB' % (t, unit, 'i' if iec else '')
    else:
        # for sizes > 1000 YB, show all digits
        return '%d %c%sB' % (int(n), unit, 'i' if iec else '')


def fsize(f):
    """Get size of an open file (must be seekable)."""
    oldpos = f.tell()
    try:
        f.seek(0, os.SEEK_END)
        return f.tell()
    finally:
        f.seek(oldpos)


def readexactly(f, size):
    """Read an exact number of bytes from a file."""
    ret = f.read(size)
    if len(ret) != size:
        raise IOError('unexpected end of data')
    return ret


def readupto(f, delim, keep=False):
    """Read from a file up to a delimiter byte.

    The delimiter will be consumed, but it won't appear in the result,
    unless 'keep' is True.
    """
    ret = ''
    while True:
        c = readexactly(f, 1)
        if c == delim:
            if keep:
                ret += c
            return ret
        ret += c

    
def listfiles(path):
    """Generate names of files."""
    for s in os.listdir(path):
        if os.path.isfile(os.path.join(path, s)):
            yield s


def listdirs(path):
    """Generate names of directories."""
    for s in os.listdir(path):
        if os.path.isdir(os.path.join(path, s)):
            yield s


@contextlib.contextmanager
def tempchdir(path=None):
    """Save and restore the current directory, optionally setting a new one."""
    oldpath = os.getcwd()
    if path is not None:
        os.chdir(path)
    yield
    os.chdir(oldpath)


# FIXME: better names
PY_EPOCH = long(WinTime.pythonEpochToFileTime())  # FILETIME of Python/C epoch
PY_TIME_SCALE = 1 / 10000000.0  # factor to convert FILETIME to seconds


##def winToPyTime(n):
##    '''Convert a FindFileW.Info date (FILETIME int64)
##    to Python seconds since the epoch.'''
##    return (n - PY_EPOCH) * PY_TIME_SCALE


def wintime_to_pyseconds(n):
    """Convert a Windows FILETIME int64 to Python seconds."""
    return (n - PY_EPOCH) * PY_TIME_SCALE


def pyseconds_to_wintime(n):
    """Convert Python seconds to a Windows FILETIME int64."""
    return int(n / PY_TIME_SCALE + PY_EPOCH)
