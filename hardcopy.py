"""Copy files as hard links."""

import os
import sys
import glob
import argparse
import errno

import win32file

import CommonTools
import pathutil


'''
hardcopy -b "E:\tv series (new)\MythBusters" "MythBusters - Season ?" "E:\tv series (new)\out"

hardcopy "..\foo.*" bar
'''


#def gen_files_wild(dirpath, reldir, mask):


def makedirs_exist_ok(path):
    """Call os.makedirs() but don't throw if the leaf already exists and is a dir."""
    try:
        os.makedirs(os.path.abspath(path))  # make sure makedirs() doesn't get os.pardir
    except OSError as err:
        if err.errno == errno.EEXIST and os.path.isdir(path):
            return
        raise


def make_hard_link(src, dst, makeunique=False):
    # FIXME: move unique name generation in 'except', use loop and return final name,
    #        -OR- let caller handle collisions
    if makeunique:
        dst = pathutil.get_unique_file(dst)
    try:
        win32file.CreateHardLink(dst, src)
        return True
    except win32file.error as err:
        CommonTools.errln(str(err))
        return False



def copy_items(src, dst, args, depth=0):

    try:
        makedirs_exist_ok(dst)
    except OSError as e:
        CommonTools.errln('could not create destination dir: ' + str(e))
        return False

    if os.path.isdir(src):
        src = os.path.join(src, '*')

    allok = True
    for s in os.listdir(srcdir):
        src = os.path.join(srcdir, s)
        dst = os.path.join(dstdir, s)
        if os.path.isfile(src):
            if not make_hard_link(src, dst, opts.gen_unique_names):
                allok = False
        elif opts.recurse and (opts.recurse_limit == 0 or depth < opts.recurse_limit):
            copy_items(src, dst, opts, depth + 1)
    return allok        


def parse_arg():
    """Parse command line."""
    parser = argparse.ArgumentParser(
        description='copy files as hard links',
        add_help=False)
    _add = parser.add_argument
    _add('-s', dest='recurse', action='store_true', 
         help='recurse source subdirectories')
    _add('-l', dest='recurse_limit', type=int, default=0, metavar='NUM',
         help='depth limit for subdirectory recursion; default is 0 (no limit)')
    _add('-f', dest='flatten', action='store_true', 
         help='flatten directory structure (ignore parent paths)')
##    _add('-g', dest='glob', action='store_true', 
##         help='enable globbing; by default only filename wildcards are expanded')
    _add('-u', dest='gen_unique_names', action='store_true', 
         help='generate unique names to avoid collisions')
    _add('-v', action='store_true', dest='verbose',
         help='print the names of files and directories moved')
    _add('-?', action='help', 
         help='this help')
##        _add('-m', type='string', dest='mask', metavar='MASK',
##             help='Include file mask.')
##        _add('-M', type='string', dest='mask', metavar='MASK',
##             help='Exclude file mask.')
    _add('sources', metavar='SRC', nargs='+',
         help='source file or directory; wildcards allowed; no parent references allowed')
    _add('dest', metavar='DST',
         help='destination directory (will be created if needed)')
##    _add('-g', dest='glob_sources', metavar='GLOBSRC', action='append',
##         help='glob sources')

    args = parser.parse_args()
    
    if args.recurse_limit < 0:
        args.recurse_limit = 0

    for s in args.sources:
        if os.pardir in pathutil.split_all(s):
            parser.error('source path must not include parent ref: "%s"' % (s))

    return args


##class Stats:
##    copiedfiles = 0
##    failedfiles = 0
##    faileddirs = 0


if __name__ == '__main__':
    args = parse_arg()
    raise RuntimeError('script not ready')

    # pop the options that are only needed here
    sources = args.__dict__.pop('sources')
    dest = args.__dict__.pop('dest')

    goterrors = False
    for src in sources:
        if not copy_items(src, dest, args):
            goterrors = True

    if goterrors:
        sys.exit(1)
