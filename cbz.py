"""Convert directories to CBZ files.

For each subdirectory in the specified directory create a CBZ file
containing all its files (local only; no subdir recursion).

Generated CBZ files are uncompressed.
"""

import os
import sys
import zipfile
import argparse
import CommonTools


def parse_args():
    ap = argparse.ArgumentParser(description='make CBZ files from subdirectory files')
    add = ap.add_argument
    add('dirs', metavar='DIR', nargs='+',
        help='parent directory whose subdirs to process')
    add('-o', dest='outdir',
        help='output directory; by default, the parent directories are used')
    return ap.parse_args()


def make_cbz_from_dir(zippath, dirpath):
    z = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_STORED)
    for s in CommonTools.listfiles(dirpath):
        z.write(os.path.join(dirpath, s), s)
    z.close()


if __name__ == '__main__':
    args = parse_args()

    if args.outdir and not os.path.isdir(args.outdir):
        try:
            os.makedirs(args.outdir)
        except os.error as x:
            print >>sys.stderr, 'could not create output dir;', x
            sys.exit(1)

    for parent in args.dirs:

        if not os.path.isdir(parent):
            print >>sys.stderr, 'parent doesn\'t exist: "%s"' % parent
            continue
        
        for dirname in CommonTools.listdirs(parent):
            dirpath = os.path.join(parent, dirname)
            zippath = os.path.join(args.outdir or parent, dirname) + '.cbz'
            print 'processing "%s" => "%s"' % (dirpath, zippath)
            make_cbz_from_dir(zippath, dirpath)
