"""Recursively move nested files to a single directory."""

import os
import sys
import shutil
import optparse

import CommonTools
import dirutil


def flatten(srcroot, opt):
    allok = True
    dstdir = opt.outdir or srcroot
    # walk bottom-up to allow dir deletion, if needed
    for path, dirs, files in os.walk(srcroot, topdown=False):
        # move files (unless we're at the destination)
        if path != dstdir:
            for s in files:
                try:
                    src = os.path.join(path, s)
                    dst = dirutil.uniquepath(os.path.join(dstdir, s))
                    if opt.keeporiginals:
                        shutil.copyfile(src, dst)
                    else:
                        shutil.move(src, dst)
                except IOError, x:
                    CommonTools.errln(str(x))
                    allok = False
                    if not opt.errorcontinue:
                        return allok
        if not opt.keeporiginals:
            # remove all dirs (they should be empty by now)
            for s in dirs:
                try:
                    os.rmdir(os.path.join(path, s))
                except IOError, x:
                    CommonTools.errln(str(x))
                    allok = False
                    if not opt.errorcontinue:
                        return allok
    return allok


def parse_cmdline():
    op = optparse.OptionParser(
        usage='%prog [options] DIRS',
        description='Move nested files from multiple subdirectories to a single directory.',
        epilog='DIRS is a list of the directories to flatten. '
               'The files of each directory are moved to that directory, unless -o is used. '
               'Name collisions are resolved by appending a unique number in parentheses after the original file name.',
        add_help_option=False)

    add = op.add_option
    add('-o', dest='outdir', 
        help='Output directory; will be created if needed. If omitted, files '
             'are moved to the top of their respective directory.')
    add('-k', dest='keeporiginals', action='store_true', 
        help='Keep original files and empty directories. If omitted, files are '
             'moved instead of copied and empty directories are deleted.')
    add('-c', dest='errorcontinue', action='store_true', 
        help='Continue processing in case of an error. By default, the first '
             'error ends the script.')
    add('-j', dest='join', 
        help='Uses the specified string to join the name of the parent dirs '
             'in front of each filename. Useful to avoid collisions or to '
             'keep the dir names as part of the output.')
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)

    opt, args = op.parse_args()

    if not args:
        op.error('at least one directory must be specified')
    args = map(unicode, args)  # necessary for proper dir listings

    return opt, args


if __name__ == '__main__':
    opt, args = parse_cmdline()

    if opt.join is not None:
        # TODO: implement this
        CommonTools.exiterror('parent name joining not supported yet')

    if opt.outdir is not None and not os.path.isdir(opt.outdir):
        if hasParentRef(opt.outdir):  # os.makedirs() can't handle this
            CommonTools.exiterror('cannot create output dir, due to embedded ".."', 2)
        try:
            os.makedirs(opt.outdir)
        except OSError, x:
            CommonTools.exiterror('cannot create output dir: ' + str(x))

    allok = True
    for s in dirs:
        if not flatten(s, opt):
            allok = False
    sys.exit(0 if allok else 1)
