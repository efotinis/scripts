#!python3
"""Perform operation on randomly selected files or dirs.

Available operations:
    - copy (default)
    - move
    - hardlink
    - shell link (create .LNK file)
"""

import argparse
import os
import random
import shutil

import efutil
from pywintypes import com_error
import shellutil
import win32file


COPY, MOVE, HARDLINK, SHELLLINK = 'cmhl'


def getargs():
    ap = argparse.ArgumentParser(
        description='perform operation on randomly selected files or dirs')
    add = ap.add_argument
    add('src', help='source directory; must exist')
    add('dst', help='target directory; will be created if needed')
    add('count', type=int, help='maximum number of files to move')
    operations = COPY, MOVE, HARDLINK, SHELLLINK
    add('-o', dest='operation', choices=operations, default=COPY,
        help='operation to perfom; one of: c=copy (default), m=move, '
        'h=hardlink, l=shell link')
    add('-d', dest='dodirs', action='store_true',
        help='process dirs instead of files')
    args = ap.parse_args()
    if not os.path.isdir(args.src):
        ap.error('source dir does not exist')
    try:
        os.makedirs(args.dst)
    except FileExistsError:
        pass
    except OSError as x:
        ap.error('could not create target dir; ' + str(x))
    if args.count <= 0:
        ap.error('count must be > 0')
    if args.dodirs and args.operation == HARDLINK:
        ap.error('dir hardlinking is not implemented yet')
    return args


def randomnames(dpath, count, files=False, dirs=False):
    """Get at most 'count' random names from dir 'dpath'."""
    if files and dirs:
        match = lambda path: True
    elif files:
        match = lambda path: os.path.isfile(path)
    elif dirs:
        match = lambda path: os.path.isdir(path)
    else:
        raise ValueError('nothing to select')
    names = [s for s in os.listdir(dpath) if match(os.path.join(dpath, s))]
    if len(names) > count:
        names = random.sample(names, count)
    return names


def main(args):
    _files, _dirs = (False, True) if args.dodirs else (True, False)
    for s in randomnames(args.src, args.count, files=_files, dirs=_dirs):
        src = os.path.join(args.src, s)
        dst = os.path.join(args.dst, s)
        try:
            if args.operation == COPY:
                if os.path.isfile(src):
                    shutil.copyfile(src, dst)
                else:
                    shutil.copytree(src, dst)
            elif args.operation == MOVE:
                os.rename(src, dst)
            elif args.operation == HARDLINK:
                if os.path.isfile(src):
                    win32file.CreateHardLink(dst, src)
                else:
                    raise NotImplementedError
            elif args.operation == SHELLLINK:
                dst = os.path.splitext(dst)[0] + '.lnk'
                shellutil.create_shortcut(dst, target=os.path.abspath(src))
        except (OSError, win32file.error, com_error) as x:
            efutil.conout('FAIL: ' + s)
            efutil.conerr(str(x))
        else:
            efutil.conout('OK:   ' + s)


if __name__ == '__main__':
    main(getargs())
