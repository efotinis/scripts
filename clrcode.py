"""Output colorized source code."""

import argparse
import sys
import os

import pygments
import pygments.lexers
import pygments.util

import conclr
import console

from pygments.token import Token


def parse_args():
    ap = argparse.ArgumentParser(
        description='print code with syntax highlighting'
    )
    ap.add_argument(
        '-l',
        dest='lexer',
        help='syntax lexer to use; if omitted it will be deduced '
            'from the input filename extensions; must be specifed for STDIN'
    )
    ap.add_argument(
        '-e',
        dest='encoding',
        help='text encoding of input files'
    )
    ap.add_argument(
        '-p',
        dest='fullpath',
        action='store_true',
        help='show full path in header instead of just file name'
    )
    ap.add_argument(
        'files',
        nargs='+',
        help='input files; use "-" for STDIN'
    )
    args = ap.parse_args()
    if args.lexer:
        try:
            args.lexer = pygments.lexers.get_lexer_by_name(args.lexer)
        except pygments.util.ClassNotFound as x:
            ap.error(x)
    return args


# NOTE: Order is significant, since some tokens are specializations
# (e.g. Number is actually Literal.Number).
# Use sorted(pygments.token.STANDARD_TYPES.keys()) for full list.
TOKEN_COLORS = {
    Token.Error:        'r+',
    Token.Other:        'r',
    Token.Keyword:      'g',
    Token.Name:         'c+',
    #Token.Literal.Number
    #Token.Literal.String
    Token.Literal:      'c',
    Token.Operator:     'y',
    Token.Punctuation:  'w',
    Token.Comment:      'm+'
}
TOKEN_COLORS = { k: conclr.attr(v) for k, v in TOKEN_COLORS.items() }


def get_token_attr(ttype, default):
    for k, v in TOKEN_COLORS.items():
        if ttype in k:
            return v | (default & 0xf0)
    return default


class Error(Exception):
    pass


def getdata(path, encoding, lexer):
    if path == '-':
        text = sys.stdin.read()
        if not lexer:
            raise Error('no lexer specified for STDIN')
    else:
        with open(path, encoding=encoding) as f:
            text = f.read()
        if not lexer:
            try:
                lexer = pygments.lexers.guess_lexer_for_filename(path, text)
            except pygments.util.ClassNotFound as x:
                raise Error(f'no lexer found for {path}')
    return text, lexer


def swapAttr(n):
    """Swap foreground and background colors."""
    fg, bg = n & 0xf, (n & 0xf0) >> 4
    return (fg << 4) + bg


def print_colored_line(out, text, outAttr, defAttr):
    # print without EOL and flush to apply
    out.settextattr(outAttr)
    print(text, end='', flush=True)
    # print EOL with default attr in case of scrolling
    out.settextattr(defAttr)
    print('')


def main(args):

    out = console.get_stdout()

    defAttr = out.gettextattr()
    hdrAttr = swapAttr(defAttr)

    for path in args.files:

        try:
            text, lexer = getdata(path, args.encoding, args.lexer)
        except Error as x:
            print(x, file=sys.stderr)
            continue

        if path == '-':
            name = '<STDIN>'
        elif args.fullpath:
            name = path
        else:
            name = os.path.basename(path)

        print_colored_line(out, f'{name} [{lexer.name}]', hdrAttr, defAttr)

        for ttype, value in pygments.lex(text, lexer):
            out.settextattr(get_token_attr(ttype, defAttr))
            out.write(value)


if __name__ == '__main__':
    main(parse_args())
