"""HOTCOPY an open FLV file."""

import os, sys
from glob import glob
from CommonTools import prettysize

def select_file(mask):
    """Select a file or return None."""
    a = glob(mask)
    for i, s in enumerate(a):
        print '%d. %s  [%s]' % (i + 1, s, prettysize(os.path.getsize(s)))
    print '0. Exit'
    while True:
        try:
            n = int(raw_input('Select file: '))
            if n == 0:
                return None
            elif not 1 <= n <= len(a):
                raise ValueError
            return a[n - 1]
        except ValueError:
            print 'ERROR: invalid selection'


def hotcopy(src, dst):
    srcdir, srcfile = os.path.split(src)
    dstdir, dstfile = os.path.split(dst)
    if not srcdir: srcdir = '.'
    if not dstdir: dstdir = '.'
    cmd = 'cmd /c hotcopy "%s" "%s" "%s" "%s"' % (
        srcdir, dstdir, srcfile, dstfile)
    os.system(cmd)
    

def main(args):
    if '/?' in args:
        print 'HOTCOPY an open FLV file.'
        print 'usage: FLV'
        raise SystemExit
    if args:
        raise SystemExit('no arguments required')

    try:
        srcdir = os.environ['TEMP']
        mask = 'fla*'

        s = select_file(os.path.join(srcdir, mask))
        if not s:
            sys.exit()
        src = os.path.join(srcdir, s)
        
        s = raw_input('Dest path: ')
        if not s:
            sys.exit()
        dst = s
        if os.path.splitext(dst)[1].lower() != '.flv':
            dst += '.flv'

        hotcopy(src, dst)

    except KeyboardInterrupt:
        raise SystemExit('aborted by user')


main(sys.argv[1:])
