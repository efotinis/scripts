"""Common script utilities."""

import os
import sys
import math
import itertools
import re
import collections
import operator

import win32console

import win32time
import binutil

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


def exiterror(msg, status=1):
    """Print error msg and exit with specified status."""
    errln(msg)
    sys.exit(status)


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


# FIXME: better names
# TODO: move to win32time
PY_EPOCH = win32time.pythonEpochToFileTime().getvalue()  # FILETIME of Python/C epoch
PY_TIME_SCALE = 1 / 10000000.0  # factor to convert FILETIME to seconds


def wintime_to_pyseconds(n):
    """Convert a Windows FILETIME uint64 to Python seconds."""
    return (n - PY_EPOCH) * PY_TIME_SCALE


def pyseconds_to_wintime(n):
    """Convert Python seconds to a Windows FILETIME uint64."""
    return int(n / PY_TIME_SCALE + PY_EPOCH)


def fileattrchars(n):
    """String of chars from a DWORD of Windows file attributes.

    Only documented/unreserved flags are returned:
        0x00000001  FILE_ATTRIBUTE_READONLY             R
        0x00000002  FILE_ATTRIBUTE_HIDDEN               H
        0x00000004  FILE_ATTRIBUTE_SYSTEM               S
        0x00000008  (undocumented)
        0x00000010  FILE_ATTRIBUTE_DIRECTORY            D
        0x00000020  FILE_ATTRIBUTE_ARCHIVE              A
        0x00000040  FILE_ATTRIBUTE_DEVICE (reserved)
        0x00000080  FILE_ATTRIBUTE_NORMAL               N
        0x00000100  FILE_ATTRIBUTE_TEMPORARY            T
        0x00000200  FILE_ATTRIBUTE_SPARSE_FILE          X
        0x00000400  FILE_ATTRIBUTE_REPARSE_POINT        P
        0x00000800  FILE_ATTRIBUTE_COMPRESSED           C
        0x00001000  FILE_ATTRIBUTE_OFFLINE              O
        0x00002000  FILE_ATTRIBUTE_NOT_CONTENT_INDEXED  I
        0x00004000  FILE_ATTRIBUTE_ENCRYPTED            E
        0x00008000  (undocumented)
        0x00010000  FILE_ATTRIBUTE_VIRTUAL              V
    """                                            
    return binutil.flagchars(n, 32, 'RHS DA NTXPCOIE V')


def nukeglobals(keep=None):
    """Clean up __main__'s namespace.

    Names in the 'keep' sequence and double-underscore ones are preserved.
    Useful when the interactive prompt gets crowded.
    """
    # find the __main__ module globals
    for i in itertools.count():
        main_globals = sys._getframe(i).f_globals
        if main_globals['__name__'] == '__main__':
            break
    # remove items
    keep = keep or []
    for item in main_globals.keys():
        if not re.match(r'__.+__', item) and item not in keep:
            del main_globals[item]


class Counter(object):
    """Counter of objects, using an optional key.

    Example:
    >>> c = Counter(key=str.lower)
    >>> c.addall('abcbcbb')
    >>> c.dump()
    1 a
    2 c
    4 b
    """
    
    def __init__(self, key=None):
        self.data = collections.defaultdict(int)
        self.key = key
        
    def add(self, x):
        """Add an item."""
        self.data[self.key(x) if self.key else x] += 1
        
    def addall(self, seq):
        """Add a sequence of items."""
        for x in seq:
            self.add(x)
            
    def clear(self):
        """Reset all."""
        self.data.clear()
        
    def _data(self):
        """Return value/counter pairs sorted by counter."""
        return sorted(self.data.items(), key=operator.itemgetter(1))
    
    def __iter__(self):
        """Iterator of value/counter pairs by increasing counter order."""
        return iter(self._data())
    
    def __reversed__(self):
        """Iterator of value/counter pairs by decreasing counter order."""
        return reversed(self._data())
    
    def dump(self):
        """Print values and counters."""
        for x, freq in self:
            print '%d %s' % (freq, x)

