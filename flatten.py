# 2006.01.27  create
# 2007.09.28  added DosCmdLine and /O,/K,/P switches

"""Recursively move nested files to a single directory."""

import os, sys, shutil
import DosCmdLine


##
##        Swtc('P', 'prefix',
##             'Prefix names of moved files with their directory path. A '
##             'separator string may be specifed; it defaults to ", ".',
##             None, value_opt=True, converter=lambda s: ', ' if s is None else s),

def flatten(srcroot, opt):
    allok = True
    dstdir = opt.outdir or srcroot
    for path, dirs, files in os.walk(srcroot, False):  # note that we're doing a bottom-up walk
        # move files (unless we're at the destination)
        if path != dstdir:
            for s in files:
                try:
                    src = os.path.join(path, s)
                    dst = getUniqueName(os.path.join(dstdir, s))
                    if opt.keep:
                        shutil.copyfile(src, dst)
                    else:
                        shutil.move(src, dst)
                except IOError, x:
                    errln(str(x))
                    allok = False
                    if not opt.errContinue:
                        return allok
        # remove all dirs (should be empty by now)
        if not opt.keep:
            for s in dirs:
                try:
                    os.rmdir(os.path.join(path, s))
                except IOError, x:
                    errln(str(x))
                    allok = False
                    if not opt.errContinue:
                        return allok
    return allok


def getUniqueName(path):
    """Generate a unique file name by adding a parenthesized number before the extension."""
    i = 1
    while os.path.isfile(path):
        base, ext = os.path.splitext(path)
        i += 1
        path = base + ' (' + str(i) + ')' + ext
    return path


##args = [unicode(s) for s in sys.argv[1:]]
##for s in args:
##    flatten(s)


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def showHelp(switches):
    name = 'FLATTEN'
    table = '\n'.join(DosCmdLine.helptable(switches))
    print """\
Move nested files from multiple subdirectories to a single directory.
Elias Fotinis 2006-2007

%s [/O:outdir] [/K] [/P[:sep]] dirs

%s

Name collisions are resolved by appending a unique number in parentheses after 
the original file name.

Exit code: 0=ok, 1=error, 2=bad param.""" % (name, table)


def main(args):
    Flag = DosCmdLine.Flag
    Swtc = DosCmdLine.Switch
    switches = (
        Swtc('O', 'outdir',
             'Output directory; will be created if needed. If omitted, files '
             'are moved to the top of their respective directory.',
             None),
        Flag('K', 'keep',
             'Keep original files and empty directories. If omitted, files are '
             'moved instead of copied and empty directories are deleted.'),
        Flag('C', 'errContinue',
             'Continue processing in case of an error. By default, the first '
             'error ends the script.'),
        Swtc('P', 'prefix',
             'Prefix names of moved files with their directory path. A '
             'separator string may be specifed; it defaults to ", ".',
             None, value_opt=True, converter=lambda s: ', ' if s is None else s),
        Flag('dirs', None,
             'A list of one or more directories to be flatten. Use "." to '
             'specify the current directory. The files of each directory are '
             'moved to that directory, unless /O is used; in that case all '
             'specified files are moved to the output directory.'),
    )
    if '/?' in args:
        showHelp(switches)
        return 0
    try:
        opt, dirs = DosCmdLine.parse(args, switches)
        dirs = map(unicode, dirs)  # necessary for proper dir listings
        if not dirs:
            raise DosCmdLine.Error('at least one directory must be specified')
    except DosCmdLine.Error, x:
        errln(str(x))
        return 2
    
##    print 'dirs:', dirs
##    print 'opt:'
##    opt.dump()
##    
##    return 0

    if opt.prefix is not None:
        errln('prefixing not supported yet')
        return 1

    if opt.outdir is not None and not os.path.isdir(opt.outdir):
        if hasParentRef(opt.outdir):  # os.makedirs() can't handle this
            errln('cannot create output dir, due to embedded ".."')
            return 2
        try:
            os.makedirs(opt.outdir)
        except OSError, x:
            errln('cannot create output dir: ' + str(x))
            return 1

    allok = True
    for s in dirs:
        if not flatten(s, opt):
            allok = False
    return 0 if allok else 1
        

sys.exit(main(sys.argv[1:]))
