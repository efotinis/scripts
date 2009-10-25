import os, sys


HOBOPATH = r'c:\Users\Elias\Program Files\HoboCopy-1.0.0.0-W2K3-Vista-32bit-Release\HoboCopy.exe'
USAGESTR = '''Copy an open or locked file using HOBOCOPY.  EF 2008

HOTCOPY src dst'''


def main(args):
    if '/?' in args:
        print USAGESTR
        return 0
    if len(args) != 2:
        sys.stderr.write('error: 2 arguments required\n')
        return 2
    srcdir, srcname = os.path.split(args[0])
    dstdir, dstname = os.path.split(args[1])
    tmpdst = os.path.join(dstdir, srcname)
    if not os.path.exists(args[0]):
        sys.stderr.write('error: source does not exist\n')
        return 2
    if os.path.exists(tmpdst):
        sys.stderr.write('error: intermediate destination already exists\n')
        return 2
    if os.path.exists(args[1]):
        sys.stderr.write('error: destination already exists\n')
        return 2
    cmd = 'cmd /c ""%s" "%s" "%s" "%s""' % (HOBOPATH, srcdir, dstdir, srcname)
    res = os.system(cmd)
    if res:
        sys.stderr.write('error: HOBOCOPY failed (%d)\n' % res)
        return 1
    try:
        os.rename(tmpdst, args[1])
    except IOError:
        sys.stderr.write('error: could not rename intermediate destination\n')
        return 1
    return 0


sys.exit(main(sys.argv[1:]))
