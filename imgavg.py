"""Average a group of images."""

import os
import sys
import argparse
import glob
import itertools
from PIL import Image


def parse_args():
    ap = argparse.ArgumentParser(
        description='calculate the average of a group of images',
        epilog='the result is grayscale')
    add = ap.add_argument
    add('input', nargs='+',
        help='input images glob; if a directory is specified, all its files '
        'are used; all images must have the same size')
    add('-o', dest='output',
        help='output image; if omitted, the result is only shown temporarily')
    add('-q', dest='quality', type=int, default=75, 
        help='output quality (if needed by format); default: %(default)s')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    size, data, count = None, None, 0
    for patt in args.input:
        if os.path.isdir(patt):
            patt = os.path.join(patt, '*')
        fnames = [s for s in glob.glob(patt) if os.path.isfile(s)]
        if not fnames:
            print >>sys.stderr, 'no files match "%s"' % patt
            continue
        for fname in fnames:
            im = Image.open(fname).convert('F')
            if not count:
                size = im.size
                data = [0] * (size[0] * size[1])
            if im.size != size:
                sys.exit('size mismatch for "%s"; expected %s; got %s' % (
                    fname, size, im.size))
            data = [n1+n2 for n1,n2 in itertools.izip(data, im.getdata())]
            count += 1
            sys.stdout.write('.')
    if not count:
        sys.exit('no images processed')
    print

    data = [n/count for n in data]
    res = Image.new('F', size)
    res.putdata(data)

    if args.output is None:
        res.show()
    else:
        res.convert('L').save(args.output, quality=args.quality)
