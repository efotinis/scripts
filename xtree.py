"""Directory tree printer.

Inspired by:
    <http://redd.it/67wfw>
    "Quick, what does the following Unix/Linux command do?"
"""

import os
import sys
import argparse
from CommonTools import scriptname, errln, uprint


ASCII_BRANCH_CHARS = '|   +-\-'
EXT_BRANCH_CHARS = u'\u2502   \u251C\u2500\u2514\u2500'


class BranchSet:
    def __init__(self, chars, indent):
        if len(chars) != 8:
            raise ValueError('BranchSet chars length must be 8')
        if indent < 1:
            raise ValueError('BranchSet indent must be >= 1')
        expand = lambda s: s[0] + s[1] * (indent-1)
        parts = (chars[i:i+2] for i in range(0,8,2))
        a = map(expand, parts)
        self.PARENT, self.LASTPARENT, self.CHILD, self.LASTCHILD = a
    def parent(self, islast):
        return self.LASTPARENT if islast else self.PARENT
    def child(self, islast):
        return self.LASTCHILD if islast else self.CHILD


def subdirs(dpath):
    """Generate the names of a directory's subdirs."""
    for s in os.listdir(unicode(dpath)):  # this may throw if access is denied
        if os.path.isdir(os.path.join(dpath, s)):
            yield s


def dumpsubs(dpath, branches, args):
    """Recursively print the tree."""
    subs = tuple(subdirs(dpath))  # we need to know when we reach the last value
    pad = ''.join(args.branches.parent(b) for b in branches)
    for s in subs:
        islast = s == subs[-1]
        uprint(pad + args.branches.child(islast) + s)
        if args.level == 0 or len(branches) + 1 < args.level:
            dumpsubs(os.path.join(dpath, s), branches + [islast], args)


def parse_args():
    ap = argparse.ArgumentParser(
        description='display graphical directory structure',
        add_help=False)
    add = ap.add_argument
    add('-a', dest='ascii', action='store_true',
        help='use ASCII for line-drawing instead of extended chars')
    add('-i', dest='indent', type=int, default=4,
        help='indentation size (>=1); default: %(default)s')
    add('-l', dest='level', type=int, default=0,
        help='maximum recursion level (0 for infinite); default: %(default)s')
    add('paths', nargs='*', default=['.'],
        help='one or more directories to scan; default: "."')
    add('-?', action='help',
        help='this help')
    args = ap.parse_args()
    if args.indent < 1:
        ap.error('indent must be >=1')
    if args.level < 0:
        ap.error('level must be >=0')
    return args


if __name__ == '__main__':
    args = parse_args()
    args.branches = BranchSet(
        ASCII_BRANCH_CHARS if args.ascii else EXT_BRANCH_CHARS,
        args.indent)
    for root in args.paths:
        uprint(root)
        dumpsubs(root, [], args)
