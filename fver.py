"""Show file version information."""

# TODO: enum all the available string values;
#       currently only well-known strings are used

import os
import sys
import optparse

import win32api

import binutil
import VerResUtils


INDENT = 4 * ' '


def _verstr(num, wordcount):
    """Convert a version number to string; words are 16 bits."""
    a = []
    for i in range(wordcount):
        a += [num & 0xffff]
        num >>= 16
    return '.'.join(map(str, reversed(a)))


def verstr32(n):
    return _verstr(n, 2)


def verstr64(n):
    return _verstr(n, 4)


VS_FF_DEBUG        = 0x00000001L
VS_FF_PRERELEASE   = 0x00000002L
VS_FF_PATCHED      = 0x00000004L
VS_FF_PRIVATEBUILD = 0x00000008L
VS_FF_INFOINFERRED = 0x00000010L
VS_FF_SPECIALBUILD = 0x00000020L
flags = {
    VS_FF_DEBUG:        'debug',
    VS_FF_PRERELEASE:   'pre-release',
    VS_FF_PATCHED:      'patched',
    VS_FF_PRIVATEBUILD: 'private build',
    VS_FF_INFOINFERRED: 'info inferred',
    VS_FF_SPECIALBUILD: 'special build'}

VOS_UNKNOWN       = 0x00000000L
VOS_DOS           = 0x00010000L
VOS_OS216         = 0x00020000L
VOS_OS232         = 0x00030000L
VOS_NT            = 0x00040000L
VOS_WINCE         = 0x00050000L

VOS__BASE         = 0x00000000L
VOS__WINDOWS16    = 0x00000001L
VOS__PM16         = 0x00000002L
VOS__PM32         = 0x00000003L
VOS__WINDOWS32    = 0x00000004L

type_high = {
    VOS_UNKNOWN: 'unknown',
    VOS_DOS:     'MS-DOS',
    VOS_OS216:   'OS/2 (16-bit)',
    VOS_OS232:   'OS/2 (32-bit)',
    VOS_NT:      'Windows NT',
    VOS_WINCE:   'Windows CE'}

type_low = {
    VOS__BASE:      '(base)',
    VOS__WINDOWS16: '16-bit Windows',
    VOS__PM16:      '16-bit Presentation Manager',
    VOS__PM32:      '32-bit Presentation Manager',
    VOS__WINDOWS32: '32-bit Windows'}


def os_str(n):
    return '%s / %s' % (
        type_high.get(n & 0xffff0000, '?'),
        type_low.get(n & 0xffff, '?'))


VFT_UNKNOWN    = 0x00000000L
VFT_APP        = 0x00000001L
VFT_DLL        = 0x00000002L
VFT_DRV        = 0x00000003L
VFT_FONT       = 0x00000004L
VFT_VXD        = 0x00000005L
VFT_STATIC_LIB = 0x00000007L

types = {
    VFT_UNKNOWN:    'unknown',
    VFT_APP:        'application',
    VFT_DLL:        'dynamic-link library',
    VFT_DRV:        'device driver',
    VFT_FONT:       'font',
    VFT_VXD:        'virtual device',
    VFT_STATIC_LIB: 'static-link library'}

VFT2_UNKNOWN         = 0x00000000L
VFT2_DRV_PRINTER     = 0x00000001L
VFT2_DRV_KEYBOARD    = 0x00000002L
VFT2_DRV_LANGUAGE    = 0x00000003L
VFT2_DRV_DISPLAY     = 0x00000004L
VFT2_DRV_MOUSE       = 0x00000005L
VFT2_DRV_NETWORK     = 0x00000006L
VFT2_DRV_SYSTEM      = 0x00000007L
VFT2_DRV_INSTALLABLE = 0x00000008L
VFT2_DRV_SOUND       = 0x00000009L
VFT2_DRV_COMM        = 0x0000000AL
VFT2_DRV_INPUTMETHOD = 0x0000000BL
VFT2_DRV_VERSIONED_PRINTER = 0x0000000CL

drvtypes = {
    VFT2_UNKNOWN:         'unknown',
    VFT2_DRV_PRINTER:     'printer',
    VFT2_DRV_KEYBOARD:    'keyboard',
    VFT2_DRV_LANGUAGE:    'language',
    VFT2_DRV_DISPLAY:     'display',
    VFT2_DRV_MOUSE:       'mouse',
    VFT2_DRV_NETWORK:     'network',
    VFT2_DRV_SYSTEM:      'system',
    VFT2_DRV_INSTALLABLE: 'installable',
    VFT2_DRV_SOUND:       'sound',
    VFT2_DRV_COMM:        'communications',
    VFT2_DRV_INPUTMETHOD: 'input method',
    VFT2_DRV_VERSIONED_PRINTER: 'versioned printer'}

VFT2_FONT_RASTER   = 0x00000001L
VFT2_FONT_VECTOR   = 0x00000002L
VFT2_FONT_TRUETYPE = 0x00000003L

fonttypes = {
    VFT2_UNKNOWN:       'unknown',
    VFT2_FONT_RASTER:   'raster',
    VFT2_FONT_VECTOR:   'vector',
    VFT2_FONT_TRUETYPE: 'TrueType'}
    
def type_str(type, subtype):
    s = types.get(type, hex(type))
    if type == VFT_DRV:
        s += ' (%s)' % drvtypes.get(subtype, hex(subtype))
    elif type == VFT_FONT:
        s += ' (%s)' % fonttypes.get(subtype, hex(subtype))
    elif type == VFT_VXD:
        s += ' (ID:%s)' % hex(subtype)
    return s


# predefined string values
defvalnames = (
    'Comments',
    'CompanyName',
    'FileDescription',
    'FileVersion',
    'InternalName',
    'LegalCopyright',
    'LegalTrademarks',
    'OriginalFilename',
    'ProductName',
    'ProductVersion',
    'PrivateBuild',
    'SpecialBuild')


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def printfixed(d):
    print INDENT + '        signature:', '0x%08X' % binutil.uint32(d['Signature'])
    print INDENT + 'structure version:', verstr32(d['StrucVersion'])
    print INDENT + '     file version:', verstr64(d['FileVersionMS'] << 32 | d['FileVersionLS'])
    print INDENT + '  product version:', verstr64(d['ProductVersionMS'] << 32 | d['ProductVersionLS'])
    print INDENT + '            flags:', binutil.flagstr(d['FileFlags'] & d['FileFlagsMask'], 32, flags)
    print INDENT + '               OS:', os_str(d['FileOS'])
    print INDENT + '             type:', type_str(d['FileType'], d['FileSubtype'])
    print INDENT + '             date:', d['FileDate'] or ''


def printvalues(fname, opt, showvals):
    d = win32api.GetFileVersionInfo(fname, '\\')
    if opt.fixed:
        printfixed(d)
    showxlats = win32api.GetFileVersionInfo(fname, '\\VarFileInfo\\Translation')
    if not opt.allxlats:
        showxlats = showxlats[:1]
    showvals_maxlen = max(map(len, showvals)) if showvals else 0
    for lang, cp in showxlats:
        xlatstr = '%04X%04X' % (lang, cp)
        print '[%s: %s, %s]' % (xlatstr,
            VerResUtils.verlangname(lang), VerResUtils.codepagename(cp))
        for name in showvals:
            val = win32api.GetFileVersionInfo(fname,
                '\\StringFileInfo\\' + xlatstr + '\\' + name)
            if val:
                # HACK: VS6/71 seem to just interleave \0 bytes instead of
                # storing as true Unicode; thus the encoding to latin1
                # (it just disgards the NULs, since \u0000...\u00ff == latin1)
                val = val.encode('latin1')
                print INDENT + name.rjust(showvals_maxlen) + ':', val


def parse_cmdline():
    op = optparse.OptionParser(
        usage='%prog [options] FILES',
        description='Display Windows version resource information.',
        epilog=None,
        add_help_option=False)
    add = op.add_option
    add('-f', dest='fixed', action='store_true',
        help='Include fixed version info.')
    add('-s', dest='strings', action='append',
        help='Show only the specified, comma-separated strings. Option is cumulative.'
             'By default, the 12 predefined ones are shown.')
    add('-t', dest='allxlats', action='store_true',
        help='Show all tanslations. By default, only the first is shown.')
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)
    return op.parse_args()

    
def main(args):
    try:
        opt, args = parse_cmdline()
        opt.strings = [s.strip() for s in ','.join(opt.strings).split(',')]
    except optparse.OptParseError as err:
        CommonTools.exiterror(str(err), 2)

    showvals = opt.strings or defvalnames  # use predef if none specified
    showvals = [s for s in showvals if s]  # remove empty (bad for GetFileVersionInfo)

    failed = False
    for fname in files:
        print fname
        try:
            if not os.path.exists(fname):
                errln('file not found: "%s"' % fname)
                failed = True
            else:
                printvalues(fname, opt, showvals)
        except win32api.error, x:
            errln('%s: "%s"' % (x[2].rstrip('.'), fname))
            failed = True

    return 1 if failed else 0


sys.exit(main(sys.argv[1:]))
