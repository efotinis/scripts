"""Recursively move nested files to a single directory."""

import os
import sys
import shutil
import argparse
import glob

import CommonTools
import pathutil
import six


def splitall(path):
    """Return list of all elements in path. Path must not be absolute."""
    # TODO: move to pathutil and unit-test
    if os.path.isabs(path):
        raise ValueError('absolute path passed to splitall()')
    a = []
    drive, path = os.path.splitdrive(path)
    while path:
        path, s = os.path.split(path)
        a += [s]
    if drive:
        a += [drive]
    a.reverse()
    return a


##def flatten(srcroot, opt):
##    allok = True
##    dstdir = opt.outdir or srcroot
##    actionfunc = shutil.copyfile if opt.keeporiginals else shutil.move
##    srcroot = os.path.normpath(srcroot)  # remove any trailing dir separator
##    # walk bottom-up to allow dir deletion, if needed;
##    for path, dirs, files in os.walk(srcroot, topdown=False):
##        # move files (unless we're at the destination)
##        if path != dstdir:
##            for s in files:
##                try:
##                    src = os.path.join(path, s)
##                    if opt.joiner is None:
##                        dst = os.path.join(dstdir, s)
##                    else:
##                        # get current relpath;
##                        # path[len(srcroot):] produces '' for the root and '/...' for the rest;
##                        # normpath() converts '' to '.';
##                        # finally, [1:] strips the first char ('.' for root, '/' for others)
##                        relpath = os.path.normpath(path[len(srcroot):])[1:]
##                        fname = opt.joiner.join(splitall(relpath) + [s])
##                        dst = os.path.join(dstdir, fname)
##                    dst = pathutil.get_unique_file(dst)
##                    actionfunc(src, dst)
##                except IOError as x:
##                    CommonTools.errln(str(x))
##                    allok = False
##                    if not opt.errorcontinue:
##                        return allok
##        if not opt.keeporiginals:
##            # remove all dirs (they should be empty by now)
##            for s in dirs:
##                try:
##                    os.rmdir(os.path.join(path, s))
##                except IOError as x:
##                    CommonTools.errln(str(x))
##                    allok = False
##                    if not opt.errorcontinue:
##                        return allok
##    return allok


def flatten(patt, opt):
    match_count = 0
    for s in glob.iglob(patt):
        match_count += 1
        print s
    if not match_count:
        print >>sys.stderr, 'WARNING: nothing matched "%s"' % patt
    return True


def parse_cmdline():
    ap = argparse.ArgumentParser(
        description='move/copy/hardlink multiple files to a single directory',
        add_help=False)

    add = ap.add_argument
    add('sources', metavar='GLOB', nargs='+',
        help='the source glob patterns')
    add('-o', dest='outdir', default='.',
        help='output directory; will be created if needed; default: "%(default)s"')

    add('-a', dest='action', choices='mch', default='m',
        help='the action to perform on each file; one of: m=move, c=copy, h=hardlink; '
             'default: "%(default)s"')

##    add('-k', dest='keeporiginals', action='store_true', 
##        help='Keep original files and empty directories. If omitted, files are '
##             'moved instead of copied and emptied directories are deleted.')
##    add('-c', dest='errorcontinue', action='store_true', 
##        help='Continue processing in case of an error. By default, the first '
##             'error ends the script.')
##    add('-j', dest='joiner', 
##        help='Uses the specified string to join the name of the parent dirs '
##             'in front of each filename. Useful to avoid collisions or to '
##             'keep the dir names as part of the output.')
    add('-?', action='help',
        help='this help')

    args = ap.parse_args()

    #if not args:
    #    ap.error('at least one directory must be specified')
    args.sources = map(six.text_type, args.sources)  # necessary for proper dir listings

    return args


if __name__ == '__main__':
    args = parse_cmdline()
##    print args
##    sys.exit('script under construction')

    # NOTE: os.pardir elements may confuse os.makedirs(), although sometimes it works fine;
    #       should we check and warn the user?
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    allok = True
    for s in args.sources:
        if not flatten(s, args):
            allok = False
    sys.exit(0 if allok else 1)
