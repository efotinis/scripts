# 2006.02.21  created
# 2007.09.25  utilized DosCmdLine; added support for paths longer than MAX_PATH;
#             minor revisions
# 2008.07.12  use CommonTools.uprint for output to handle unicode;
#             added /ACP

# BUG: '.' doesn't display cur dir

import os
import sys
import locale
#import glob
import re
import DosCmdLine
import FindFileW
import CommonTools


MAX_PATH = 260
RAWPATH_PFX = '\\\\?\\'  # allows system funcs to accept paths longer than MAX_PATH


def getsize(path):
    """Get the size of a file, even if len(path) > MAX_PATH."""
    if len(path) <= MAX_PATH:
        return os.path.getsize(path)
    # os.path.getsize uses os.stat, which doesn't accept a '\\?\' prefix;
    # so we have to use FindXxxFile
    info = FindFileW.getInfo(RAWPATH_PFX + path)
    ret = info.nFileSizeLow
    if info.nFileSizeHigh:
        ret += info.nFileSizeHigh << 32
    return ret


def deepDir(root):
    """Returns the total dirs, files and bytes in the specified dir."""
    #assert type(root) == unicode
    dirsCnt = filesCnt = bytes = 0
    # Use abspath() to remove '.' and '..'. Otherwise, join() may result
    # in paths longer than MAX_PATH and stat() in getsize() will fail.
    # normpath() isn't sufficient, because it can't remove leading '.' or '..'.
    # Note that using the absolute path in os.walk() is a bit slower,
    # but the loop runs faster because we don't have to normpath()
    # when joining paths with filenames!
    for path, dirs, files in os.walk(os.path.abspath(root)):
        #assert type(path) == unicode
        filesCnt += len(files)
        dirsCnt  += len(dirs)
        #bytes    += sum([os.path.getsize(os.path.join(path, s)) for s in files])
        for s in files:
            #assert type(s) == unicode
            file = os.path.join(path, s)
##            try:
##                bytes += os.path.getsize(NO_MAXPATH_PFX + file)
##            except OSError:
##                sys.stderr.write('Could not access "%s"\n' % file)
##                sys.exit(1)
            bytes += getsize(file)
    return dirsCnt, filesCnt, bytes


# A kind of listdir+glob.
# Accepts *only* DOS wildcards ('?*')
# and only in the last part of the path (unlike glob).
# However, it also returns the path spec, like glob.
# Rules for 'wildcard':
# - it's always assumed to be a dir
# - a trailing '\' is ignored (unless the whole string is '\', which means the root)
def getDirs(wildcard):
    #assert type(wildcard) == unicode

    # trim w/s and normalize
    # conv to unicode is a HACK, because normpath(u'.') returns '.'
    wildcard = unicode(os.path.normpath(wildcard.strip()))

    # remove trailing '\' unless it's the only char in the str
    if len(wildcard) > 1 and wildcard[-1:] == '\\':
        wildcard = wildcard[0:-1]
    
    path, mask = os.path.split(wildcard)

    # return as-is if there are no wildcards    
    if not '*' in mask and not '?' in mask:
        return [wildcard]
    
    # build (and use) regex only if needed
    rx = (doswild2re(mask) if mask and mask <> '*' else None)
    
    # HACK for Python bug 818059;
    # if an empty _unicode_ string is used, listdir() treats it like u'\\'
    dummyDotAdded = False
    if not path:
    	path = type(wildcard)('.')
    	dummyDotAdded = True

    ret = []
    for s in os.listdir(path):
        item = os.path.join(path, s)
        if os.path.isdir(item) and (not rx or rx.match(s)):
            ret.append(item)

    # remove dummy '.\'
    if dummyDotAdded:
        ret = [s[2:] for s in ret]
    
    return ret


def doswild2re(s):
    """Return a case-ignoring regexp from a DOS wildcard."""
    ret, i, length = type(s)(''), 0, len(s)
    for c in s:
        if   c == '*': ret += '.*'
        elif c == '?': ret += '.'
        else:          ret += re.escape(c)
    return re.compile(ret, re.I)


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def showhelp(switches):
    name = os.path.basename(sys.argv[0]).upper()
    swlist = '\n'.join(DosCmdLine.helptable(switches))
    print """\
Prints the total subdirs, files, and bytes of the specified dirs.
Elias Fotinis 2006-2007

%s [U:unit] [/D:decs] [/L:locale] [dirs ...]

%s

Exit code: 0=ok, 1=error, 2=bad params""" % (name, swlist)


def main(args):
    Flag = DosCmdLine.Flag
    Swtc = DosCmdLine.Switch
    switches = (
        Flag('?', 'help', None),
        Swtc('U', 'unit',
             'The output size unit. One of "K", "M", "G". Default is bytes.',
              1, converter=lambda s:1024**(1+'KMG'.index(s.upper()))),
        Swtc('D', 'decs',
             'Number of output decimal digits. Ignored for bytes.'
             'Valid range is 0-10. Default is 2.',
             2, converter=int),
        Swtc('L', 'locale',
             'The locale to use. Defaults to the system locale (""). '
             'Apart from the "C" locale, locale names are system dependant. '
             'They are also case-sensitive.',
             ''),
        Flag('ACP', 'acp',
             'Force output to ANSI codepage.'),
        Flag('dirs', None,
             'The dirs to process. Wildcards allowed. Default is the current dir.'),
    )
    try:
        opt, dirs = DosCmdLine.parse(args, switches)
        if opt.help:
            showhelp(switches)
            return 0
        if not 0 <= opt.decs <= 10:
            raise DosCmdLine.Error('decimals out of range')
    except DosCmdLine.Error, x:
        errln(str(x))
        return 2
    try:
        locale.setlocale(locale.LC_ALL, opt.locale)
    except locale.Error:
        errln('invalid locale: "%s"' % opt.locale)
        return 2

    # convert paths to Unicode (it'd be nice if Python had 'sys.wargv')
    # so that dir traversing functions will also return Unicode
    dirs = [unicode(s, 'mbcs') for s in dirs]
    
    # no decimals if unit is bytes
    if opt.unit == 1:
        opt.decs = 0

    if not dirs:
        dirs = [u'.']

    if opt.acp:
        def print_func(s):
            print s.encode('mbcs')
    else:
        print_func = lambda s: CommonTools.uprint(s)

    for mask in dirs:
        # can't use glob() because it skips items starting with '.'
        # (although the '[]' matching would be nice)
        for s in getDirs(mask):
            # just a convenience check for the use;
            # a race condition can still fool this
            if not os.path.isdir(s):
                sys.stderr.write('Invalid directory: "%s"\n' % s)
                continue
            t = deepDir(s)
            # PYTHON BUG: locale.format outputs the wrong width for ints
            # when grouping is on; this doesn't happen with floats.
            # That's why t[0]/t[1] are converted to float.
            print_func(locale.format_string('%10.0f %10.0f %15.*f',
                (float(t[0]), float(t[1]), opt.decs, t[2] / float(opt.unit)),
                True) + ' ' + s)


sys.exit(main(sys.argv[1:]))
