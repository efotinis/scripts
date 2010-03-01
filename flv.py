"""Copy a locked Flash video.

When viewing a Flash video in a browser, the Flash player plugin
stores the file in the %TEMP% directory and locks it, preventing
normal copying. So, we use the HOTCOPY batch, which in turn uses
the HOBOCOPY utility to copy the video to a specified directory.
"""

import os
import sys
import getopt
from glob import glob
import CommonTools


def select_file(mask):
    """Interactive file selection; return path or None."""
    a = glob(mask)
    for i, s in enumerate(a):
        print '%d. %s  [%s]' % (i + 1, s, CommonTools.prettysize(os.path.getsize(s)))
    while True:
        try:
            s = raw_input('Select file (Enter to exit): ')
            if not s:
                return None
            n = int(s)
            if not 1 <= n <= len(a):
                raise ValueError
            return a[n - 1]
        except ValueError:
            print 'ERROR: invalid selection'


def hotcopy(src, dst):
    """HOTCOPY a source file path to a destination file path."""
    srcdir, srcfile = os.path.split(src)
    dstdir, dstfile = os.path.split(dst)
    if not srcdir: srcdir = '.'
    if not dstdir: dstdir = '.'
    cmd = 'cmd /c hotcopy.cmd "%s" "%s" "%s" "%s"' % (
        srcdir, dstdir, srcfile, dstfile)
    os.system(cmd)


def parse_cmdline():
    try:
        opt, args = getopt.gnu_getopt(sys.argv[1:], '?d')
        if args:
            raise getopt.GetoptError('no arguments required')
    except getopt.GetoptError as err:
        raise SystemExit('ERROR: ' + str(err))
    opt = dict(opt)
    if '-?' in opt:
        print __doc__.split('\n', 1)[0]
        print 'usage: FLV [-d?]'
        print ''
        print '  -d  Use current user\'s desktop if no directory is specified for output.'
        print '  -?  This help.'
        raise SystemExit
    return opt, args
    

if __name__ == '__main__':
    opt, args = parse_cmdline()
    try:
        srcdir = os.environ['TEMP']
        mask = 'fla*.tmp'  # fname format: 'fla%X.tmp' % n, where 0<=n<=0xffff
        s = select_file(os.path.join(srcdir, mask))
        if not s:
            sys.exit()
        src = os.path.join(srcdir, s)
        
        s = raw_input('Output file (Enter to exit): ').strip()
        if not s:
            sys.exit()
        if s[:1] == s[-1:] == '"':
            s = s[1:-1]
        dst = s
        if os.path.splitext(dst)[1].lower() != '.flv':
            dst += '.flv'
        if not os.path.dirname(dst) and '-d' in opt:
            dst = os.path.join(CommonTools.getDesktop(), dst)

        hotcopy(src, dst)

    except KeyboardInterrupt:
        raise SystemExit('aborted by user')
