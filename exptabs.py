"""Replace tabs with spaces.

tags: text
compat: 2.7+, 3.3+
platform: any
"""

import os
import sys
import argparse

import efutil


def parse_args():
    ap = argparse.ArgumentParser(
        description='replace tabs with spaces')
    add = ap.add_argument
    # NOTE: Don't use argparse.FileType, mainly to avoid overwriting
    #   an existing output file. Another problem is that FileType is
    #   too eager to open the file (even, for example, if -h is used
    #   after the file args, or an invalid option is specified).
    #   http://bugs.python.org/issue13824 suggests a fix using a new 
    #   class (FileContext), but until that gets implemented (if it
    #   does) we better use plain path strings.
    add('input', 
        help='input file; "-" for stdin')
    add('output', default='-', nargs='?', 
        help='output file; must be different from input; '
        '"-" (default) for stdout')
    add('-s', dest='tabsize', type=int, default=4, 
        help='tab size; default: %(default)s')
    add('-b', dest='onlybeg', action='store_true', 
        help='replace tabs only at the beginning of each line')
    add('-o', dest='overwrite', action='store_true', 
        help='overwrite output file if it exists')
    args = ap.parse_args()

    # detect same input/output (only paths are checked)
    if args.input != '-' or args.output != '-':
        s1 = os.path.normcase(os.path.normpath(args.input))
        s2 = os.path.normcase(os.path.normpath(args.output))
        if s1 == s2:
            ap.error('input and output files must be different')

    if os.path.exists(args.output) and not args.overwrite:
        ap.error('output file exists; use -o to overwrite')

    args.input = efutil.FileArg(args.input, 'r')
    args.output = efutil.FileArg(args.output, 'w')

    return args


def count_leading(s, char):
    """Number of multiple leading chars in a string."""
    count = 0
    for c in s:
        if c != char:
            break
        count += 1
    return count


def expand_tabs(s, tabsize, leading_only=False):
    if leading_only:
        n = count_leading(s, '\t')
        return max(0, tabsize) * n * ' ' + s[n:]
    else:
        return s.expandtabs(tabsize)


if __name__ == '__main__':
    args = parse_args()
    try:
        for s in args.input:
            args.output.write(expand_tabs(s, args.tabsize, args.onlybeg))
    except IOError as x:
        sys.exit(x)
