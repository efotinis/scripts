"""Miscellaneous utilities."""

from __future__ import print_function
import collections
import contextlib
import csv
import datetime
import itertools
import os
import re
import sys
import warnings

if os.name == 'nt':
    import shellutil
    import win32console
else:
    shellutil = None
    win32console = None

import mathutil


PY2 = sys.version_info.major == 2
PY3 = sys.version_info.major == 3


if os.name == 'nt':
    def winconout():
        """Windows standard output (PyConsoleScreenBuffer) or None."""
        return win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
    def winconerr():
        """Windows standard error (PyConsoleScreenBuffer) or None."""
        return win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
else:
    winconout = None
    winconerr = None


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


class FileArg(object):
    """File-like class that handles "-" for stdin/out.

    Only a limited set of the file methods are implemented.
    """

    def __init__(self, path, mode='r', buffering=-1):
        self.path = path
        if path == '-':
            if 'r' in mode:
                self.file = sys.stdin
            else:
                self.file = sys.stdout
        else:
            self.file = open(path, mode, buffering)

    def read(self, size=-1):
        return self.file.read(size)

    def readline(self, size=-1):
        return self.file.readline(size)

    def write(self, s):
        return self.file.write(s)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        s = self.file.readline()
        if not s:
            raise StopIteration()
        return s
        
    def close(self):
        if self.path != '-':
            self.file.close()


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
    h = winconout and winconout()
    if h:
        h.WriteConsole(s + '\n')
        h.Close()
    else:
        print(s)


def conout(*a, **kw):
    """Windows 'print' replacement.

    This function tries to simulate the behavior of native Windows console
    programs and commands by:
    - outputting true Unicode when possible
    - decoding with errors='replace' to avoid UnicodeError exceptions

    Cases handled (in order):
    1. PythonWin interactive window (strings decoded via 'mbcs')
    2. Windows console (strings decoded via console output codepage)
    3. other; assumes file or pipe (Unicode encoded via console output codepage)
    
    Keyword args:
    - sep: string to output between multiple arguments; default: ' '
    - end: string to output after arguments; default: '\n'
    - error: send to stderr instead of stdout; default: False
    """
    sep = kw.pop('sep', ' ')
    end = kw.pop('end', '\n')
    error = kw.pop('error', False)
    if kw:
        raise TypeError('unexpected keyword arguments: ' + str(kw.keys()))
    if error:
        PY_STREAM = sys.stderr
        WIN_STREAM = winconerr and winconerr()
    else:
        PY_STREAM = sys.stdout
        WIN_STREAM = winconout and winconout()
    try:
        try:
            isatty = PY_STREAM.isatty()
        except AttributeError:
            # probably PythonWin's interactive window;
            # PythonWin handles Unicode property, but its sys.stdout/stderr.encoding
            # is 'utf-8'; we prefer to decode 8-bit strings with CP_ACP ('mbcs')
            encoding = 'mbcs'
            a = [s if PY3 or isinstance(s, unicode) else s.decode(encoding, 'replace')
                 for s in a]
            PY_STREAM.write(sep.join(a) + end)
            return
        if isatty and WIN_STREAM:
            # on Windows, this means the console, which is natively Unicode;
            # 8-bit strings should be decoded with the console output codepage
            encoding = 'cp' + str(win32console.GetConsoleOutputCP())
            a = [s if PY3 or isinstance(s, unicode) else s.decode(encoding)
                 for s in a]
            WIN_STREAM.WriteConsole(sep.join(a) + end)  # accepts both str and unicode
        else:
            # file or pipe; encode Unicode strings with the console output codepage
            encoding = 'cp' + str(win32console.GetConsoleOutputCP())
            a = [s.encode(encoding, 'replace') if isinstance(s, unicode) else s
                 for s in a]
            PY_STREAM.write(sep.join(a) + end)
    finally:
        if WIN_STREAM:
            WIN_STREAM.Close()


if os.name != 'nt':
    conout = print


def conerr(*a, **kw):
    """Similar to conout(), but with error=True."""
    kw['error'] = True
    conout(*a, **kw)


def gotoDesktop():
    """Change working directory to current user's desktop."""
    if os.name == 'nt':
        path = shellutil.SpecialFolders.desktop
    else:
        path = os.path.expanduser('~/Desktop')
    os.chdir(path)


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


def get_timestamp(date=None, utc=False, compact=False, fract=2):
    """Timestamp string.

    If 'date' is not provided, the current one is used (local or utc,
    depending on 'utc'). If 'compact' is true, no delimiters are used,
    except for a single dash before hours. 'fract' specifies the count
    of fractional second digits (0-6).
    """
    if date is None:
        date = datetime.datetime.utcnow() if utc else datetime.datetime.now()

    if compact:
        s = date.strftime('%Y%m%d-%H%M%S')
    else:
        s = date.strftime('%Y-%m-%d %H:%M:%S')

    if 0 < fract <= 6:
        if not compact:
            s += '.'
        s += date.strftime("%f")[:fract]

    return s


def open_csv(path, mode='r'):
    """Properly open CSV file for any Python version.

    Automatically uses binary mode and newlines='' when needed.

    NOTE: The csv module in Python 2 does not support Unicode as is. See the
    Python docs for sample wrappers.
    """
    if PY2 and 'b' not in mode:
        mode += 'b'
    kwargs = {'mode': mode}
    if PY3:
        kwargs['newline'] = ''
    return open(path, **kwargs)


def load_csv_table(f, typename, fieldnames, **converters):
    """Generate the table entries of a CSV file as namedtuple objects.

    A new namedtuple object ('typename') is created, using the
    specified field names (or the first data row, if None).

    The remaining named args are used to convert the field values, by passing
    the original string value. Not all fields need to be converted, but the
    specified ones are checked for existance.
    """
    reader = csv.reader(f)
    if fieldnames is None:
        fieldnames = reader.next()
    rec_type = collections.namedtuple(typename, fieldnames)
    fieldnames = rec_type._fields

    # replace converter keys with field name indices
    for name in list(converters.keys()):  # need copy of keys
        try:
            i = fieldnames.index(name)
        except ValueError:
            raise ValueError('converter name not in fields', name, fieldnames)
        converters[i] = converters[name]
        del converters[name]

    for row in reader:
        for i, func in converters.items():
            row[i] = func(row[i])
        yield rec_type(*row)


def promote_input_to_unicode(s, wildcard=False, nonpath=False):
    """Check string for potential encoding errors and promote to Unicode.

    This is useful in Python 2 on Windows where command line arguments are
    implicitly converted to the system ANSI codepage, producing replacement
    '?' characters. If such characters are found, an exception is raised.
    If 'wildcard' or 'nonpath' are true, the string may contain actual '?'
    characters, making detection impossible. In this case, only a warning
    is printed.

    Note that the 'wildcard' and 'nonpath' params are mainly used for
    documenting intent.

    Promotion to Unicode ensures that subsequent system calls will use the
    Unicode WinAPI functions.

    Does nothing on non-Windows or non-Python-2 platforms.
    """
    if sys.platform == 'win32' and sys.version_info.major == 2:
        if '?' in s:
            msg = 'replacement characters found in input string'
            if wildcard or nonpath:
                warnings.warn(msg)
            else:
                raise ValueError(msg)
        s = unicode(s)
    return s


def pluralize(n, singular, plural=None):
    """Return singular or plural form based on count.

    If no plural is specified, an 's' is appended to the singular.
    """
    if n == 1:
        return singular
    elif plural is None:
        return singular + 's'
    else:
        return plural


TIMEFMT_PARTS = {
    'ms': (1, (60,)),
    'hm': (60, (60,)),
    'hms': (1, (60,60)),
    'dh': (3600, (24,)),
    'dhm': (60, (24, 60)),
    'dhms': (1, (24, 60, 60)),
}


def timefmt(seconds, parts='hms', sep=':', labels=None):
    """Format seconds to string of various formats.

    Labels can be a string sequence or True to use the part chars.
    """
    div0, divs = TIMEFMT_PARTS[parts]
    n = round(seconds / div0)
    a = mathutil.multi_divmod(n, *divs)
    if labels is None:
        labels = [''] * len(parts)
    elif labels is True:
        labels = parts
    return sep.join(format(n, '02') + s for n, s in zip(a, labels))


def _strip_label(s, label):
    if not label:
        return s
    if s.endswith(label):
        return s[:-len(label)]
    raise ValueError('"{}" is missing label "{}"'.format(s, label))


def timeparse(s, parts='hms', sep=':', labels=None):
    """Parse a string of various formats to seconds.

    Labels can be a string sequence or True to use the part chars.
    """
    a = s.split(sep)
    if len(a) != len(parts):
        raise ValueError('parts count mismatch')
    if labels is True:
        labels = parts
    if labels is not None:
        a = [_strip_label(s, l) for s, l in zip(a, labels)]
    a = [int(s) for s in a]
    mul0, muls = TIMEFMT_PARTS[parts]
    n = a[0]
    for m, mul in zip(a[1:], muls):
        n = n * mul + m
    return n * mul0


def size_arg(s):
    """Size argument type for argparse."""
    s = s.strip()
    SUFFIXES = 'kmgtpe'
    i = SUFFIXES.find(s[-1:]) + 1
    if i:
        s = s[:-1]
    multiplier = 1024 ** i
    return int(float(s) * multiplier)


def frame_count(path):
    """Count GIF frames."""
    from PIL import Image
    with Image.open(path) as im:
        with contextlib.suppress(EOFError):
            for i in itertools.count():
                im.seek(i)
        return im.tell()


def redact(obj, shallow=False, keys=None, replace='(...)'):
    """Remove dict values from JSON object.

    obj:        source object
    shallow:    do not recurse into dict values
    keys:       sequence of dict keys whose values are redacted
    replace:    replacement object
    """
    if isinstance(obj, dict):
        for k in obj:
            if keys is not None and k in keys:
                obj[k] = replace
            elif isinstance(obj[k], (dict, list)):
                redact(obj[k], shallow, keys, replace)
    elif isinstance(obj, list):
        for x in obj:
            redact(x, shallow, keys, replace)
