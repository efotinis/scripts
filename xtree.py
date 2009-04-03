# 2008/02/08  Created; inspired by the reddit thread
#             "Quick, what does the following Unix/Linux command do?"
#             <http://reddit.com/goto?rss=true&id=t3_67wfw>
# 2008.03.09  moved 'uprint' to CommonTools

import os, sys
import DosCmdLine
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
    for s in os.listdir(unicode(dpath)):  # 
        if os.path.isdir(os.path.join(dpath, s)):
            yield s


def dumpsubs(dpath, branches, opt):
    """Recursively print the tree."""
    subs = tuple(subdirs(dpath))  # we need to know when we reach the last value
    pad = ''.join(opt.branches.parent(b) for b in branches)
    for s in subs:
        islast = s == subs[-1]
        uprint(pad + opt.branches.child(islast) + s)
        if opt.level == 0 or len(branches) + 1 < opt.level:
            dumpsubs(os.path.join(dpath, s), branches + [islast], opt)


def buildswitches():
    """Create the cmdline switches."""
    Flag, Swch = DosCmdLine.Flag, DosCmdLine.Switch
    return (
        Flag('A', 'ascii',
             'Use ASCII instead of extended line-drawing chars.'),
        Swch('I', 'indent',
             'Indentation size (>=1). Default is 4.',
             4, converter=int),
        Swch('L', 'level',
             'The maximum level of recursion. Default is 0, meaning no limit.',
             0, converter=int),
        Flag('paths', '',
             'One or more directories to scan. Default is the current one.'))


def showhelp(switches):
    """Print help."""
    print """Display graphical directory structure.

%s [/A] [/I:indent] [/L:level] [paths]

%s""" % (
    scriptname().upper(),
    '\n'.join(DosCmdLine.helptable(switches)))


def main(args):
    switches = buildswitches()
    if '/?' in args:
        showhelp(switches)
        return 0
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if not params:
            params = ['.']
        if opt.level < 0:
            raise DosCmdLine.Error('recursion level must be >= 0')
        if opt.indent < 1:
            raise DosCmdLine.Error('indent must be >= 1')
    except DosCmdLine.Error, x:
        errln(str(x))
        return 2
    setattr(opt, 'branches',
            BranchSet(ASCII_BRANCH_CHARS if opt.ascii else EXT_BRANCH_CHARS,
                      opt.indent))
    for root in params:
        uprint(root)
        dumpsubs(root, [], opt)


sys.exit(main(sys.argv[1:]))
