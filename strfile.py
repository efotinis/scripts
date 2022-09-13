"""Python implementation of Unix strfile."""

import argparse
import os
import struct
import sys


def parse_args():
    p = argparse.ArgumentParser(
        description='Implementation of Unix strfile command.'
    )
    p.add_argument(
        '-C',
        dest='comments',
        action='store_true',
        help='Treat lines starting with two delimiter characters as comments. '
             'Currently such comments are simply discarded.'
    )
    p.add_argument(
        '-c',
        dest='delimiter',
        type=str,
        default='%',
        help='Set delimiter character. Default is "%(default)s".'
    )
    p.add_argument(
        '-i',
        dest='ignorecase',
        action='store_true',
        help='Ignore case when ordering strings.'
    )
    p.add_argument(
        '-o',
        dest='sort',
        action='store_true',
        help='Order table entries by alphabetical order. '
             'Initial non-alphabetic characters are ignored.'
    )
    p.add_argument(
        '-r',
        dest='randomize',
        action='store_true',
        help='Randomize table entries. This option overrides -o.'
    )
    p.add_argument(
        '-s',
        dest='silent',
        action='store_true',
        help='Do not output summary message on completion.'
    )
    p.add_argument(
        '-x',
        dest='rot13',
        action='store_true',
        help='Rotate ASCII alphabetic characters by 13 positions (ROT13).'
    )
    p.add_argument(
        'source',
        help='Source file.'
    )
    p.add_argument(
        'output',
        nargs='?',
        help='Output file. If not specified it default to the source file '
             'with a ".dat" extension.'
    )
    args = p.parse_args()
    if len(args.delimiter) != 1:
        p.error('Delimiter must be a single character.')
    if args.output is None:
        stem, ext = os.path.splitext(args.source)
        args.output = stem + '.dat'
    p1 = os.path.normpath(os.path.abspath(args.source))
    p2 = os.path.normpath(os.path.abspath(args.output))
    if p1 == p2:
        p.error('Source and output file paths are the same.')
    return args


if __name__ == '__main__':
    args = parse_args()

    # TODO: handle options:
    #   - ignorecase
    #   - sort
    #   - randomize
    #   - rot13

    HEADER = '>LLLLLc3s'
    HEADER_LEN = struct.calcsize(HEADER)

    fout = open(args.output, 'wb')
    fout.write('\0' * HEADER_LEN)
    fout.write(struct.pack('>L', 0))

    count = 0
    minsize = 2**31
    maxsize = 0

    delim_line = args.delim_line + '\n'

    def is_comment_line(s, comments, delimiter):
        return comments and s.startswith(delimiter * 2)

    curpos, lastpos = 0, 0
    fin = open(args.source, 'rt')
    for s in fin:
        curpos += len(s)
        # TODO: may need to rework size calc to account for comments
        if is_comment_line(s, args.comments, args.delimiter):
            continue
        if s == delim_line:
            fout.write(struct.pack('>L', curpos))
            count += 1
            size = curpos - lastpos - 2
            assert size >= 0, fin.tell()
            if size < minsize: minsize = size
            if size > maxsize: maxsize = size
            lastpos = curpos

    assert fin.tell() == lastpos, 'file does not end with a delimiter'

    version = 1
    flags = 0
    delim = '%'
    padding = '\0' * 3
    hdr = struct.pack(HEADER, version, count, maxsize, minsize, flags, delim, padding)
    fout.seek(0)
    fout.write(hdr)

    if not args.silent:
        print('source:', args.source)
        print('output:', args.ouput)
        print('  entries: ', count)
        print('  min size: ', minsize)
        print('  max size: ', maxsize)
