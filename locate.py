"""Uses PATH and PATHEXT to locate Windows executables."""

from __future__ import print_function
import os
import sys
import argparse
import itertools


def get_envlist(s):
    """Split and return a PATH-like (';'-delimited) env var; [] on error."""
    try:
        return os.environ[s].split(';')
    except KeyError:
        return []


def errln(s):
    """Write error line to STDERR."""
    sys.stderr.write('ERROR: ' + s + '\n')


def locate_file(name, exts, dirs, find_all):
    """Search for file with extension in dirs and return list of found paths."""
    ret = []
    for (dir_, ext) in itertools.product(dirs, exts):
        s = os.path.join(dir_, name + ext)
        if os.path.isfile(s):
            ret += [s]
            if not find_all:
                break
    return ret


def parse_args():
    parser = argparse.ArgumentParser(
        description='locate executable files using the PATH and PATHEXT')
    add = parser.add_argument

    add('-a', dest='findall', action='store_true',
       help='locate all occurences; by default, only the first one is shown')
    add('-b', dest='absolute', action='store_true',
       help='output absolute paths')
    add('-v', dest='verbose', action='store_true',
       help='verbose output; includes the input names')
    add('files', metavar='FILE', nargs='+',
       help='the file name to locate; directories and wildcards are not allowed')

    args = parser.parse_args()
    
    for s in args.files:
        if os.path.dirname(s):
            parser.error('directory path not allowed: "%s"' % s)
        if '?' in s or '*' in s:
            parser.error('wildcards not allowed: "%s"' % s)
            
    return args


if __name__ == '__main__':
    args = parse_args()

    # prepend '' to initially check without adding an extension
    # TODO: maybe disable this?
    path_exts = [''] + get_envlist('PATHEXT')

    # on Windows the current directory is always checked first
    path_dirs = ['.'] + get_envlist('PATH')
    
    # True when at least one on the files was not found
    not_found = False
    
    for name in args.files:
        a = locate_file(name, path_exts, path_dirs, args.findall)
        if not a:
            not_found = True
            errln('file not found: "%s"' % name)
            continue
        if args.absolute:
            a = [os.path.abspath(s) for s in a]
        if args.verbose:
            print(name)
            for s in a:
                print('  ' + s)
        else:
            for s in a:
                print(s)
            
    sys.exit(1 if not_found else 0)
