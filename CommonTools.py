"""Common script utilities."""

import os
import sys
import math
import itertools
import re
import collections
import operator

import win32console

import wintime
import shellutil

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


# TODO: move scriptname(), errln() and exiterror() at some 'scriptutil' module

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


# TODO: move WriteConsole() to some 'winconsole' module and replace this
#       with a more appropriately named function, depending on whether
#       it falls back to Python's 'print'
def uprint(s):
    """Print a unicode string followed by a newline.

    Useful for printing Unicode strings in the Windows console.
    """
    try:
        STDOUT.WriteConsole(s + '\n')
    except:
        print s


def gotoDesktop():
    """Change working directory to current user's desktop."""
    os.chdir(shellutil.SpecialFolders.desktop)


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


# TODO: move listfiles() and listdirs() to 'pathutil' module.

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
# TODO: move to wintime
PY_EPOCH = wintime.python_epoch_utc_to_filetime()  # FILETIME of Python/C epoch
PY_EPOCH = PY_EPOCH.dwLowDateTime | (PY_EPOCH.dwHighDateTime << 32)
PY_TIME_SCALE = 1 / 10000000.0  # factor to convert FILETIME to seconds


def wintime_to_pyseconds(n):
    """Convert a Windows FILETIME uint64 to Python seconds."""
    return (n - PY_EPOCH) * PY_TIME_SCALE


def pyseconds_to_wintime(n):
    """Convert Python seconds to a Windows FILETIME uint64."""
    return int(n / PY_TIME_SCALE + PY_EPOCH)


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
