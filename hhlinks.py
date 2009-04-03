# 2007.08.02  Created
# 2007.09.21  minor changes: optparse -> DosCmdLine

import os, sys
import _winreg, efRegistry, DosCmdLine

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_PARAMS = 2


class CheckError(Exception):
    def __init__(self):
        Exception.__init__(self, 'Handler is not registered.')


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def hhexepath():
    """Return the full path of HH.EXE (as if it existed.)"""
    windir = os.environ['windir'] if 'windir' in os.environ else 'C:\\Windows'
    return os.path.join(windir, 'hh.exe')


def register():
    """Write mk: protocol handler to registry."""
    hhpath = hhexepath()
    HKCR = _winreg.HKEY_CLASSES_ROOT
    SZ = _winreg.REG_SZ
    k = _winreg.CreateKey(HKCR, 'mk')
    _winreg.SetValueEx(k, '', 0, SZ, 'URL:mk Protocol')
    _winreg.SetValueEx(k, 'URL Protocol', 0, SZ, '')
    _winreg.SetValue(HKCR, 'mk\\DefaultIcon', SZ, hhpath)
    _winreg.SetValue(HKCR, 'mk\\shell\\open\\command', SZ, hhpath + ' %1')
    print 'Registered.'


def unregister():
    """Remove mk: protocol handler from registry."""
    efRegistry.nukeKey(_winreg.HKEY_CLASSES_ROOT, 'mk')
    print 'Unregistered.'


def check():
    """Test mk: protocol handler in registry."""
    haskey = efRegistry.regKeyExists
    if not haskey('HKCR\\mk'):
        raise CheckError
    try:
        HKCR = _winreg.HKEY_CLASSES_ROOT
        s = _winreg.QueryValue(HKCR, 'mk\\shell\\open\\command')
    except WindowsError:
        raise CheckError
    if s.lower() != hhexepath().lower() + ' %1':
        raise CheckError
    print 'Handler is registered.'


def showhelp(switches):
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0].upper()
    table = '\n'.join(DosCmdLine.helptable(switches))
    print """\
Register HH.EXE for launching HtmlHelp links (mk:@MSITStore:...).
Elias Fotinis 2007

%s [/R | /U | /C]

%s

ERRORLEVEL: 0=success, 1=failure, 2=param error""" % (name, table)


def main(args):
    try:
        Flag = DosCmdLine.Flag
        switches = (
            Flag('?', 'help', None),
            Flag('R', 'register', 'Register handler.'),
            Flag('U', 'unregister', 'Unregister handler.'),
            Flag('C', 'check', 'Check handler.'),
        )
        opt, params = DosCmdLine.parse(args, switches)
        if opt.help:
            showhelp(switches)
            return EXIT_OK
        if params:
            raise DosCmdLine.Error('no params are required')
        if opt.register + opt.unregister + opt.check != 1:
            raise DosCmdLine.Error('one (and only one) of /R, /U and /C is required')
    except DosCmdLine.Error, x:
        errln(str(x))
        return EXIT_BAD_PARAMS
    try:
        if opt.register:
            register()
        elif opt.unregister:
            unregister()
        else:
            check()
        return EXIT_OK
    except (CheckError, WindowsError), x:
        errln(str(x))
        return EXIT_ERROR


sys.exit(main(sys.argv[1:]))
