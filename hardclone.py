"""Clone a full directory structure using hardlinks for files."""

import os
import argparse
import win32file
import fsutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='clone dir tree using file hardlinks')
    add = ap.add_argument
    add('source', help='source directory; must exist')
    add('target', help='target directory; must not exist')
    args = ap.parse_args()
    if not os.path.exists(args.source):
        ap.error('source dir does not exist: "%s"' % args.source)
    if os.path.exists(args.target):
        ap.error('target dir exists: "%s"' % args.target)
    return args


if __name__ == '__main__':
    args = parse_args()

    for rel, _, files in fsutil.os_walk_rel(args.source):
        srcdir = os.path.join(args.source, rel)
        dstdir = os.path.join(args.target, rel)
        
        if rel == '':
            os.makedirs(dstdir)  # create full chain for top dir
        else:
            os.mkdir(dstdir)
            
        for s in files:
            existing = os.path.join(srcdir, s)
            newlink = os.path.join(dstdir, s)
            win32file.CreateHardLink(newlink, existing)
