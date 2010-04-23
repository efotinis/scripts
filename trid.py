"""Python wrapper demo of Marco Pontello's TrIDLib.

(C) 2008 Elias Fotinis
TrIDLib is (C) 2003-06 Marco Pontello
"""
import os, sys, glob
from TrIDLib import TrIDLib, Error as TrIDError


# modify these if needed to point to the DLL and the defpack
#DLL_PATH = DEFS_PATH = os.path.dirname(sys.argv[0])

##if os.environ['ComputerName'].lower() == 'efcore':
##    #DLL_PATH = DEFS_PATH = r'C:\Users\Elias\Program Files\TrID'
##    raise OSError('cannot use 32-bit DLL in 64-bit Python')
##    # TODO: ask author for 64-bit dll version
##else:
##    DLL_PATH = DEFS_PATH = os.path.join(os.environ['ProgramFiles'], 'TrID')

# try the 32-bit folder first (in case we're in Win x64)
_prgfiles = os.environ.get('ProgramFiles(x86)') or os.environ.get('ProgramFiles')
DLL_PATH = DEFS_PATH = os.path.join(_prgfiles, 'TrID')


def showhelp():
    print 'TrIDLib Python wrapper v1.0 - (C) 2008 Elias Fotinis'
    print ''
    print 'TRID.PY file [...]'
    print ''
    print '  file  One or more files to check. Glob wildcards allowed.'


def genfiles(masks):
    """Generate file paths from a list of glob masks."""
    for mask in masks:
        for path in glob.iglob(mask):
            if os.path.isfile(path):
                yield path


def main(args):
    if '/?' in args:
        showhelp()
        raise SystemExit
    try:
        trid = TrIDLib(DLL_PATH, DEFS_PATH)
    except TrIDError, x:
        raise SystemExit(str(x))

    print 'DLL version: %d.%02d' % trid.version()
    print 'definitions: %d' % trid.defsnum()
    print

    for fpath in genfiles(args):
        print fpath
        try:
            trid.submit(fpath)
            trid.analyze()
            a = trid.results()
            if not a:
                print '  (unknown type)'
            else:
                totalpts = float(sum(x[2] for x in a))
                for type, ext, points in a:
                    print '  %5.1f%%  %-13s  %s' % (
                        100.0 * points / totalpts,
                        '(' + '/'.join(ext) + ')',
                        type)
        except TrIDError, x:
            print '  ERROR: ' + str(x)
        print


main(sys.argv[1:])
