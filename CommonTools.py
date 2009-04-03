"""Common functions for "tool" scripts.

2007.11.23 EF: created
2008.03.09 EF: added 'uprint'
2008.08.03 EF: added 'splitunits'
2008.09.12 EF: added 'gotoDesktop'
2008.10.02 EF: added 'prettysize'
2008.10.11 EF: added 'getDesktop'
2008.12.27 EF: added 'fsize'
"""


import os, sys
import win32console
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
    """
    Split a number to a tuple of units. E.g.:

    # split 125sec to 2min:5sec
    >>> splitunits(125, (60,))
    (5, 2)
    
    # split 123456sec to 1days:10hrs:17min:36sec
    >>> splitunits(123456, (60,60,24))
    (36, 17, 10, 1)
    """
    ret = []
    for u in units:
        ret += [n % u]
        n /= u
    return tuple(ret + [n])


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


def prettysize(n):
    # TODO: doc
    if n < 1024:
        return '%d bytes' % n
    for unit in 'KMGTPEZY':
        n /= 1024.0
        if n < 1024:
            return '%.2f %ciB' % (n, unit)
    return '%.2f %ciB' % (n*1024.0, 'Y')


def fsize(f):
    """Get size of an open file (must be seekable)."""
    oldpos = f.tell()
    try:
        f.seek(0, os.SEEK_END)
        return f.tell()
    finally:
        f.seek(oldpos)
