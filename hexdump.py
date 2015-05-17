"""File hex dump."""

from __future__ import print_function
import argparse
import os
import efutil


def size_t(s):
    s = s.lower()
    sign = 1
    if s[:1] == '-':
        sign = -1
        s = s[1:]
    if s.startswith('0x'):
        value = int(s[2:], 16)
        unit = 1
    else:
        unit = 'kmgtpe'.find(s[-1:]) + 1
        if unit:
            unit = 1024 ** unit
            s = s[:-1]
        else:
            unit = 1
        value = int(s)
    return sign * value * unit


def read_file(path, offset, size, width):
    with open(path, 'rb') as f:
        f.seek(offset, os.SEEK_SET if offset >= 0 else os.SEEK_END)
        offset = f.tell()
        while size is None or size > 0:
            data = f.read(min(width, size) if size is not None else width)
            if not data:
                break
            yield offset, data
            offset += len(data)
            if size is not None:
                size -= len(data)


def dump(offset, data, width):
    data = [ord(c) for c in data] if efutil.PY2 else list(data)
    data += [None] * (width - len(data))
    hexstr = ' '.join('  ' if n is None else '%02x' % n for n in data)
    ascstr = ''.join(' ' if n is None else chr(n) if 32<=n<=126 else '.' for n in data)
    print(' %08x | %s | %s' % (offset, hexstr, ascstr))


def parse_args():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='file hex dump')
    add = ap.add_argument
    add('file', nargs='+',
        help='input file')
    add('-o', dest='offset', type=size_t, default=0,
        help='start offset; negative means from EOF (capped at BOF)')
    add('-s', dest='size', type=size_t, default=0,
        help='dump size; <=0 means to EOF')
    add('-w', dest='width', type=int, default=16,
        help='output line width')
    args = ap.parse_args()
    if args.size <= 0:
        args.size = None
    if args.width < 1:
        ap.error('output width must be >= 1')
    return args


if __name__ == '__main__':
    args = parse_args()
    for path in args.file:
        #efutil.conout('file: ' + path)
        print('file: ' + path)
        try:
            for offset, data in read_file(path, args.offset, args.size, args.width):
                dump(offset, data, args.width)
        except IOError as x:
            efutil.conerr(str(x))
            