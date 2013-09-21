"""Display file/subdir/byte counts of directories."""

import os
import sys
import locale
import re
import argparse

import CommonTools
import winfixargv


# TODO: cleanup needed (esp. old Python bugs)
# FIXME: '.' doesn't display cur dir
# FIXME: Unicode output


RAWPATH_PREFIX = '\\\\?\\'  # disable path parsing


def getsize(path):
    """Get the size of a file, even if len(path) > MAX_PATH."""
    try:
        return os.path.getsize(path)
    except WindowsError:
        # probably ERROR_PATH_NOT_FOUND
        return os.path.getsize(RAWPATH_PREFIX + path)


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


def parse_args():
    UNITS = 'bkmgtpe'
    ap = argparse.ArgumentParser(
        description='prints the total subdirs/files/bytes of directories',
        add_help=False)

    add = ap.add_argument

    add('-u', dest='unit', choices=UNITS, default='b',
        help='the outsize size unit; default: %(default)s')
    add('-d', dest='decs', type=int, default=2,
        help='output decimal digits (ignored for bytes); default: %(default)s')
    add('-l', dest='locale', default="",
        help='locale to use; use an empty string for the system locale; '
             'note that locale names are case-sensitive and (apart from the "C" locale) '
             'system-dependant; default: %(default)s')
    add('-a', dest='acp', action='store_true',
        help='force output to Windows ANSI codepage')
    add('dirs', nargs='*', metavar='DIR',
        help='source directory; wildcards allowed; default is the current dir')
    add('-?', action='help', help='this help')

    args = ap.parse_args()

    args.decs = min(max(0, args.decs), 10)
    args.unit = 1024 ** UNITS.index(args.unit)
    if args.unit == 1:
        args.decs = 0
    args.dirs = args.dirs or [u'.']
    #args.dirs = [unicode(s, 'mbcs') for s in args.dirs]  # FIXME: should use Unicode argv instead
    
    try:
        locale.setlocale(locale.LC_ALL, args.locale)  # FIXME: this seems to aways fail if args.locale != ""
    except locale.Error as x:
        ap.error('invalid locale "%s": %s' % (args.locale, x))

    return args


if __name__ == '__main__':

    args = parse_args()

    print args
    sys.exit()

    if args.acp:
        print_func = lambda s: sys.stdout.write(s.encode('mbcs') + '\n')
    else:
        print_func = CommonTools.uprint

    for mask in args.dirs:
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
                (float(t[0]), float(t[1]), args.decs, t[2] / float(args.unit)),
                True) + ' ' + s)
