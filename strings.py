"""Find ASCII strings in a binary file."""

import sys
import getopt
import re
import os
import contextlib
import optparse
if os.name == 'nt':
    import msvcrt

import CommonTools


DEFAULT_MINSIZE = 4
DEFAULT_MAXSIZE = None


@contextlib.contextmanager
def binary_stdin():
    """Temporarily switch STDIN to binary mode on Windows (NOP on other platforms)."""
    if os.name == 'nt':
        fd = sys.stdin.fileno()
        oldmode = msvcrt.setmode(fd, os.O_BINARY)
        try:
            yield
        finally:
            msvcrt.setmode(fd, oldmode)
    else:
        yield


def parse_cmdline():
    parser = optparse.OptionParser(
        description='Find ASCII strings in a binary file.',
        usage='%prog [options] [FILE]',
        epilog='If no file is specified, STDIN is used.',
        add_help_option=False)

    ADD = parser.add_option
    ADD('-m',
        dest='minsize', type='int', default=DEFAULT_MINSIZE,
        help='Minimum string size. Default is %default.')
    ADD('-M',
        dest='maxsize', type='int', default=DEFAULT_MAXSIZE,
        help='Maximum string size. Default is %default.')
    ADD('-b',
        dest='bare', action='store_true',
        help='Bare output (no hex offsets).')
    ADD('-?',
        action='help',
        help=optparse.SUPPRESS_HELP)

    try:
        opt, args = parser.parse_args(args=map(unicode, sys.argv[1:]))
        parser.destroy()
        if len(args) > 1:
            raise optparse.OptParseError('at most one file is accepted')
    except optparse.OptParseError as err:
        CommonTools.exiterror(str(err), 2)

    return opt, args


if __name__ == '__main__':
    opt, args = parse_cmdline()

    chars = ''.join(chr(n) for n in range(32, 128))
    sizestr = lambda n: '' if n is None else str(n)
    sizes = '%s,%s' % (sizestr(opt.minsize), sizestr(opt.maxsize))
    rx = re.compile(r'[%s]{%s}' % (re.escape(chars), sizes))

    try:
        if args:
            (fname,) = args
            dispfname = 'file "%s"' % fname
            with open(fname, 'rb') as f:
                bytes = f.read()
        else:
            dispfname = 'STDIN'
            with binary_stdin():
                bytes = sys.stdin.read()
    except IOError as err:
        CommonTools.exiterror(str(err))

    for m in rx.finditer(bytes):
        if opt.bare:
            print m.group()
        else:
            print '%08x %s' % (m.start(), m.group())
