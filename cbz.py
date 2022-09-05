"""Convert directories to CBZ files.

For each subdirectory in the specified directory create a CBZ file
containing all its files (local only; no subdir recursion).

Generated CBZ files are uncompressed.
"""

import argparse
import os
import sys
import zipfile

import efutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='make CBZ files from subdirectory files'
    )

    add = ap.add_argument
    add('dirs', metavar='DIR', nargs='+',
        help='parent directory whose subdirs to process')
    add('-o', dest='outdir',
        help='output directory; by default, the parent directories are used')

    args = ap.parse_args()

    if args.outdir and not os.path.isdir(args.outdir):
        try:
            os.makedirs(args.outdir)
        except OSError as x:
            print('could not create output dir;', x, file=sys.stderr)
            sys.exit(1)

    return args


def make_cbz_from_dir(zippath, dirpath):
    with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_STORED) as z:
        for s in efutil.listfiles(dirpath):
            z.write(os.path.join(dirpath, s), s)


if __name__ == '__main__':
    args = parse_args()

    for parent in args.dirs:
        if not os.path.isdir(parent):
            print(f'parent does not exist: "{parent}"', file=sys.stderr)
            continue
        for dirname in efutil.listdirs(parent):
            dirpath = os.path.join(parent, dirname)
            zippath = os.path.join(args.outdir or parent, dirname) + '.cbz'
            print(f'processing "{dirpath}" => "{zippath}"')
            make_cbz_from_dir(zippath, dirpath)
