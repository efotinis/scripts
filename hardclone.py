"""Clone a full directory structure using hardlinks for files."""

from __future__ import print_function
import os
import argparse
import win32file
import fsutil
import efutil
import six


def parse_args():
    ap = argparse.ArgumentParser(
        description='clone dir tree using file hardlinks')
    add = ap.add_argument

    add('source', help='source directory; must exist')
    add('target', help='target directory; must not exist')

    args = ap.parse_args()
    args.source = six.text_type(args.source)
    args.target = six.text_type(args.target)

    if not os.path.exists(args.source):
        ap.error('source dir does not exist: "%s"' % args.source)
    if os.path.exists(args.target):
        ap.error('target dir exists: "%s"' % args.target)

    return args


if __name__ == '__main__':
    args = parse_args()

    dircount, filecount, failcount = 0, 0, 0

    for rel, _, files in fsutil.os_walk_rel(args.source):
        srcdir = os.path.join(args.source, rel)
        dstdir = os.path.join(args.target, rel)
        
        if rel == '':
            os.makedirs(dstdir)  # create full chain for top dir
        else:
            os.mkdir(dstdir)
        dircount += 1
            
        for s in files:
            existing = os.path.join(srcdir, s)
            newlink = os.path.join(dstdir, s)
            try:
                win32file.CreateHardLink(newlink, existing)
                filecount += 1
            except win32file.error as x:
                efutil.conerr('could not hardlink "%s": "%s"' % (
                    os.path.join(rel, s), x))
                failcount += 1

    print('directories created:', dircount)
    print('files hardlinked:', filecount)
    print('hardlink failures:', failcount)
