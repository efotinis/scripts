"""Test files for non-ASCII chars."""

import os
import re
import sys
import codecs
import optparse
from glob import glob

import efutil


BOMS = (codecs.BOM_BE, codecs.BOM_LE, codecs.BOM_UTF8)


def parse_cmdline():
    op = optparse.OptionParser(
        usage='%prog [options] FILES',
        description='Scan text files for extended, non-ASCII chars.',
        epilog='FILES is one or more files/dirs to check; glob-style wildcards accepted. '
               'If a file contains extended characters, its name is printed, followed by '
               'a list of the characters. Returns 0 if all files are ASCII, 1 otherwise.',
        add_help_option=False)

    add = op.add_option
    add('-b', dest='bomignore', action='store_true',
        help='Ignore files with Unicode BOM (UTF-16 BE/LE or UTF-8).')
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)

    opt, args = op.parse_args()
    if not args:
        op.error('no files specified')
    return opt, args


if __name__ == '__main__':
    opt, masks = parse_cmdline()
    foundsome, ioerror = False, False
    for mask in masks:
        if os.path.isdir(mask):
            mask = os.path.join(mask, '*')
        for fspec in glob(mask):
            try:
                s = file(fspec).read()
                if opt.bomignore and s.startswith(BOMS):
                    continue
                badchars = ''.join(sorted(set(filter(lambda c: ord(c) >= 127, s))))
                if badchars:
                    print fspec
                    print '  ' + badchars
                    foundsome = True
            except IOError as x:
                efutil.errln('%s: "%s"' % (str(x), fspec))
                ioerror = True
    if foundsome or ioerror:
        sys.exit(1)
