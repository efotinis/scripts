"""Split an image to a grid of subimages."""

import os
import sys
import argparse
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(
        description='split an image to a grid of subimages',
        add_help=False)

    _add = parser.add_argument

    _add(dest='infile', metavar='SRC',
         help='input image')
    _add(dest='rows', metavar='ROWS', type=int,
         help='number of rows (>0)')
    _add(dest='cols', metavar='COLS', type=int,
         help='number of columns (>0)')
    _add('-o', dest='outfile', metavar='DST',
         help='output file; available {}-style formatting vars: '
              '"r" (row), "c" (column), "i" (row-major index), '
              '"j" (column-major index); default is "input{i}.ext"')
    _add('-f', dest='format', metavar='FMT',
         help='output image format; default depends on output extension')
    _add('--overwrite', dest='overwrite', action='store_true', 
         help='overwrite existing output files; by default an error msg is printed')
    _add('-?', action='help', help='this help')

    args = parser.parse_args()

    if args.outfile is None:
        stem, ext = os.path.splitext(args.infile)
        args.outfile = stem + '{i}' + ext

    if args.rows <= 0 or args.cols <= 0:
        parser.error('rows/columns must be >0')

    return args


if __name__ == '__main__':
    args = parse_args()

    im = Image.open(args.infile)
    width, height = im.size

    errors = 0
    for row in range(args.rows):
        for col in range(args.cols):

            # bounding rect of subimage
            x1, y1 = width * col // args.cols, height * row // args.rows
            x2, y2 = width * (col + 1) // args.cols, height * (row + 1) // args.rows

            # create subimage
            imnew = Image.new('RGB', (x2-x1, y2-y1))
            imnew.paste(im.copy().crop((x1, y1, x2, y2)))

            # format name and save output
            i = row * args.cols + col
            j = col * args.rows + row
            outpath = args.outfile.format(r=row, c=col, i=i, j=j)
            if not args.overwrite and os.path.exists(outpath):
                print >>sys.stderr, 'file already exists: "%s"' % outpath
                errors += 1
            else:
                imnew.save(outpath, format=args.format)

    sys.exit(1 if errors else 0)
