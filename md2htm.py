"""Markdown file converter."""

import argparse
import io
import os
import sys

import markdown
import win32api

import pathutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='Markdown to HTML converter')
    add = ap.add_argument

    add('input', 
        help='input file; use "" for STDIN')
    add('output', nargs='?',
        help='output file; use "" for STDOUT; defaults to STDOUT if STDIN '
        'is used as input, or to the input with a ".htm" extension otherwise')

    args = ap.parse_args()

    if args.output is None:
        if args.input == '':
            args.output = ''
        else:
            args.output = pathutil.set_ext(args.input, '.htm')
    if args.input != '' and args.output != '':
        p1 = os.path.normcase(os.path.abspath(args.input))
        p2 = os.path.normcase(os.path.abspath(args.output))
        if p1 == p2:
            ap.error('input and output paths are the same')

    return args


# FIXME: non-ascii i/o with stdin/out on Py 3 doesn't work

def read_input_file(path):
    """Read file or STDIN if path is ''."""
    if path:
        with io.open(path, 'rt', encoding='utf-8') as f:
            return f.read()
    else:
        return sys.stdin.read()


def write_output_file(path, s):
    """Write file or STDOUT if path is ''."""
    if path:
        with io.open(path, 'wt', encoding='utf-8') as f:
            f.write(s)
    else:
        sys.stdout.write(s)


if __name__ == '__main__':
    args = parse_args()
    s = markdown.markdown(read_input_file(args.input))
    write_output_file(args.output, s)
