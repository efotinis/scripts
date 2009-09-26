# Simple File Verification (SFV) tester
# EF 2007.06.23

# TODO: use a BreakOut exception for /X
# TODO: split up some funcs
# TODO: maybe use bitflags for exitcode


import os
import sys
from binascii import crc32
import wildcard


setup_instructions = """

    [HKEY_CLASSES_ROOT]
        [.sfv]
            @="sfv_auto_file"
            PerceivedType="text"  // allow generic Open/Edit cmds and searching inside
        [sfv_auto_file]
            @="File Checksum List"
            [DefaultIcon]
                @="shell32.dll,57"  // a clipboard with a pen and a tick mark
            [shell]
                @="open"  // make Open default (from PerceivedType); if missing default is Test
                [test]
                    @="&Test"
                    [command]
                        @='cmd /d /c sfv "%1" & pause'  // provided SFV.PY is in the PATH

    TODO: these should by automated
"""


EXIT_OK = 0
EXIT_FILEERROR = 1
EXIT_BADPARAM = 2
EXIT_FATAL = 3

BUFFER_SIZE = 1024**2  # for reading files


def showhelp():
    print """\
SFV [/V] [/X] [{/REG|/UNREG}] [file ...]

  file    One or more SFV files to check. Wildcards are allowed.
  /V      Verbose output. Prints the names of all files while checking them.
  /X      Exit on first error.
  /REG    TODO: Register a Test command for SFV files in the Shell.
  /UNREG  TODO: Remove the above.

Return codes:
  0  All files verified.
  1  At least one file was not found or verified.
  2  Bad program option, or SFV file not found or malformed.
  3  Fatal error."""


def main(args):

    if '/?' in args:
        showhelp()
        return EXIT_OK

    try: # parse options
        opt = Options(args)
    except Options.Error, x:
        errln(str(x))
        return EXIT_BADPARAM

    totalsfv = 0
    totalok, totalfail, totalmissing = 0, 0, 0
    errors = set()

    if (opt.register and not shellRegister() or
        opt.unregister and not shellUnregister()):
        errors.add(EXIT_FATAL)

    if not (opt.exitonerror and errors):
        for spec in opt.files:
            s1, s2 = os.path.split(spec)
            if wildcard.iswild(s2):
                files = [os.path.join(s1, s) for s in wildcard.listdir(s2, s1)]
            else:
                files = [spec]
            for s in files:
                ok,bad,missing = verify(s, opt, errors)
                if opt.exitonerror and errors:
                    break
                print 'Files OK:%d, bad:%d, missing:%d' % (ok,bad,missing)
                print
                totalok += ok
                totalfail += bad
                totalmissing += missing
                totalsfv += 1
        print 'Total files OK:%d, bad:%d, missing:%d' % (totalok, totalfail, totalmissing)
        print 'Total SFV files:%d' % (totalsfv,)

    # return highest error number, if any
    return sorted(list(errors))[-1] if errors else EXIT_OK


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


class Options:
    simpleflags = {
        'x':'exitonerror',
        'v':'verbose',
        'reg':'register',
        'unreg':'unregister'
    }
    class Error(Exception):
        pass
    def __init__(self, args):
        self.files = []
        for s in self.simpleflags.values():
            setattr(self, s, False)
        for s in args:
            if s.startswith('/'):
                self.getswitch(s[1:])
            else:
                self.files += [s]
        if self.register and self.unregister:
            raise self.Error('/REG and /UNREG are mutually exclusive')
    def getswitch(self, s):
        if s.lower() not in self.simpleflags:
            raise self.Error('invalid switch: "/' + s + '"')
        setattr(self, self.simpleflags[s.lower()], True)


def verify(sfv, opt, errors):
    """Open a SFV file and test its files.
    Return number of verified,unverified,and missing files."""
    print 'Processing SFV file "%s"' % sfv
    numok, numbad, nummissing = 0, 0, 0
    try:
        f = file(sfv)
    except IOError, x:
        errln(str(x))
        errors.add(EXIT_BADPARAM)
        return numok, numbad, nummissing
    for lineno, s in enumerate(f):
        s = s.rstrip('\n').strip()
        if s.startswith(';') or not s:  # comment or empty
            continue
        try:
            fname, chksum = parseline(s, lineno, errors)
        except ValueError:
            if opt.exitonerror:
                return numok, numbad, nummissing
        spec = os.path.join(os.path.dirname(sfv), fname)
        try:
            if opt.verbose:
                print 'Checking file "%s"' % spec
            datafile = file(spec, 'rb')
            curcrc = 0
            while True:
                buf = datafile.read(BUFFER_SIZE)
                if not buf:
                    break
                curcrc = crc32(buf, curcrc)
            curcrc &= 0xffffffff
            if curcrc == chksum:
                numok += 1
            else:
                numbad += 1
                errln('CRC mismatch for file "%s"' % spec)
                errors.add(EXIT_FILEERROR)
                if opt.exitonerror:
                    return numok, numbad, nummissing
        except IOError, x:
            nummissing += 1
            errln(str(x))
            errors.add(EXIT_FILEERROR)
            if opt.exitonerror:
                return numok, numbad, nummissing
    return numok, numbad, nummissing
            

def parseline(s, lineno, errors):
    """Parse non-empty, non-comment SFV line and return (filename, checksum).
    On error, set it in "errors" and raise ValueError."""
    # split file and checksum
    #   (note that we allow for filenames with embedded spaces
    #   eg. "my file.txt 1234ABCD" is parsed as "my file.txt" and "1234ABCD")
    tokens = s.split(' ')
    if len(tokens) < 2:
        errln('Line %d: missing checksum' % (lineno+1,))
        errors.add(EXIT_BADPARAM)
        raise ValueError
    fname = ' '.join(tokens[:-1])
    try:
        chksum = int(tokens[-1], 16)
        if (chksum & ~0xffffffff) <> 0:  # must be 32-bit
            raise ValueError
    except ValueError:
        errln('Line %d: invalid checksum "%s"' % (lineno+1,tokens[-1]))
        errors.add(EXIT_BADPARAM)
        raise
    return fname, chksum


def shellRegister():
    import _winreg
    #import efRegistry
    k1, k2 = None
    try:
        HKCR = _winreg.HKEY_CLASSES_ROOT
        setStr = lambda key, name, data: _winreg.SetValueEx(
            key, name, 0, _winreg.REG_SZ, data)
        k1 = _winreg.CreateKey(HKCR, '.sfv')
        setStr(k1, '', 'sfv_auto_file')
        setStr(k1, 'PerceivedType', 'text')
        k2 = _winreg.CreateKey(HKCR, 'sfv_auto_file')
    finally:
        if k1: _winreg.CloseKey(k1)
        if k2: _winreg.CloseKey(k2)


##
##    [HKEY_CLASSES_ROOT]
##        [.sfv]
##            @="sfv_auto_file"
##            PerceivedType="text"  // allow generic Open/Edit cmds and searching inside
##        [sfv_auto_file]
##            @="File Checksum List"
##            [DefaultIcon]
##                @="shell32.dll,57"  // a clipboard with a pen and a tick mark
##            [shell]
##                @="open"  // make Open default (from PerceivedType); if missing default is Test
##                [test]
##                    @="&Test"
##                    [command]
##                        @='cmd /d /c sfv "%1" & pause'  // provided SFV.PY is in the PATH


"""

('HKCR', (
    ('.sfv', (
        ('',STR,'sfv_auto_file'),
        ('PerceivedType',STR,'text')
    )),
    ('sfv_auto_file', (
        ('',STR,'File Checksum List'),
        ('DefaultIcon', (
            ('',STR,'shell32.dll,57'),
        )),
        ('shell', (
            ('',STR,'open'),
            ('test', (
                ('',STR,'&Test'),
                ('command', (
                    ('',STR,'cmd /d /c sfv "%1" & pause')
                )),
            )),
        )),
    )),
)
"""

import _winreg
STR = _winreg.REG_SZ
a=('HKCR', (
    ('.sfv', (
        ('',STR,'sfv_auto_file'),
        ('PerceivedType',STR,'text')
    )),
    ('sfv_auto_file', (
        ('',STR,'File Checksum List'),
        ('DefaultIcon', (
            ('',STR,'shell32.dll,57'),
        )),
        ('shell', (
            ('',STR,'open'),
            ('test', (
                ('',STR,'&Test'),
                ('command', (
                    ('',STR,'cmd /d /c sfv "%1" & pause')
                )),
            )),
        )),
    )),
))



def shellUnregister():
    import _winreg, ctypes
    from ctypes.wintypes import DWORD, HKEY, LPCWSTR
    SHDeleteKeyW = ctypes.windll.shlwapi.SHDeleteKeyW
    SHDeleteKeyW.restype = DWORD
    SHDeleteKeyW.argtypes = [HKEY, LPCWSTR]
    HKCR = _winreg.HKEY_CLASSES_ROOT
    n1 = SHDeleteKeyW(HKCR, '.sfv')
    n2 = SHDeleteKeyW(HKCR, 'sfv_auto_file')
    return n1 == 0 and n2 == 0



##sys.exit(main(sys.argv[1:]))
try:
    sys.exit(main(sys.argv[1:]))
except Exception, x:
    errln(str(x))
    sys.exit(EXIT_FATAL)
