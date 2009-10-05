"""Manage HtmlHelp link protocol."""

import os
import sys
import _winreg
import optparse

import efRegistry
import CommonTools


class CheckError(Exception):
    def __init__(self):
        Exception.__init__(self, 'Handler is not registered.')


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


def parse_cmdline():
    op = optparse.OptionParser(
        usage='%prog [options]',
        description='Register HH.EXE for launching HtmlHelp links (mk:@MSITStore:...).',
        epilog=None,
        add_help_option=False)

    add = op.add_option
    add('-r', dest='register', action='store_true', help='Register handler.')
    add('-u', dest='unregister', action='store_true', help='Unregister handler.')
    add('-c', dest='check', action='store_true', help='Check handler.')
    add('-?', action='help', help=optparse.SUPPRESS_HELP)

    opt, args = op.parse_args()

    if args:
        op.error('no params are required')
    if opt.register + opt.unregister + opt.check != 1:
        op.error('exactly one of -r, -u, or -c is required')

    return opt, args


if __name__ == '__main__':
    opt, args = parse_cmdline()
    try:
        if opt.register:
            register()
        elif opt.unregister:
            unregister()
        else:
            check()
    except (CheckError, WindowsError) as x:
        CommonTools.exiterror(str(x))
