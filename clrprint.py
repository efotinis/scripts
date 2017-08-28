#!python3
"""Write to Windows console using embedded dBase-style color codes."""

import sys
import re
import win32api
import win32console
import argparse
import contextlib


def parse_args():
    ap = argparse.ArgumentParser(
        description='output colored text'
    )
    add = ap.add_argument
    add('-N', dest='noeol', action='store_true',
        help='do not output trailing newline')
    add(dest='inputs', metavar='INPUT', nargs='+',
        help='input string; multiple values are allowed; '
        'may contain embedded color codes in brackers: "{CODE}", '
        'where CODE is a dBase-style color or these special values: '
        '"i" to invert current fg/bg, "d" to restore the default colors')
    return ap.parse_args()


COLORS = {}
for i, c in enumerate('NBGCRMYW'):
    COLORS[c] = i
    COLORS[c + '+'] = i + 8


def color_code(s):
    s = s.replace(' ', '').upper()
    if s == 'I':
        return 'invert', None, None
    if s == 'D':
        return 'default', None, None
    fore, _, back = s.partition('/')
    return 'set', COLORS.get(fore), COLORS.get(back)


class ColorState:
    def __init__(self):
        self.con = win32console.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
        self.original = self.current = self._get()
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._set(self.original)
    def _get(self):
        """Get (fore,back) console color attribute."""
        n = self.con.GetConsoleScreenBufferInfo()['Attributes']
        return n & 0xf, (n & 0xf0) >> 4
    def _set(self, fg_bg):
        """Set (fore,back) console color attribute."""
        n = (fg_bg[0] & 0xf) | ((fg_bg[1] & 0xf) << 4)
        self.con.SetConsoleTextAttribute(n)
    def change(self, code):
        cmd, fg, bg = color_code(code)
        if cmd == 'invert':
            new = self.current[1], self.current[0]
        elif cmd == 'default':
            new = self.original
        elif cmd == 'set':
            new = (self.current[0] if fg is None else fg,
                   self.current[1] if bg is None else bg)
        if new != self.current:
            self._set(new)
            self.current = new


def main(args):
    tokens = re.compile(r'(\{.*?\}|[^{]+)')  # -> "text" or "{code}"
    with ColorState() as cstate:
        for input in args.inputs:
            for s in tokens.findall(input):
                if s.startswith('{'):
                    cstate.change(s[1:-1])
                else:
                    cstate.con.WriteConsole(s)
    if not args.noeol:
        sys.stdout.write('\n')


if __name__ == '__main__':
    main(parse_args())
