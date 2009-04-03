# 2007.06.27  Created.
# 2008.01.28  Generalized; added help switch.

import os, re, sys, codecs, DosCmdLine
from glob import glob

BOMS = (codecs.BOM_BE, codecs.BOM_LE, codecs.BOM_UTF8)


def showhelp(switches):
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0].upper()
    print """\
Scan text files for extended (non-ASCII) chars.
v2008.01.28 - (C) 2007-2008 Elias Fotinis

%s [/B] mask ...
""" % name
    DosCmdLine.showlist(switches)
    print """
    
If a file contains extended chars, its name is printed, followed by a list of
the chars. Returns 0 if all files are ASCII, 1 otherwise (or in case of error),
or 2 for bad params.
"""[1:-1]
    

def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def buildswitches():
    return [
        DosCmdLine.Flag('mask', '',
            'One or more files/dirs to check. Glob-style wildcards accepted.'),
        DosCmdLine.Flag('B', 'bomignore',
            'Ignore files with Unicode BOM (UTF-16 BE/LE or UTF-8).')
    ]

    
def main(args):
    switches = buildswitches()
    if '/?' in args:
        showhelp(switches)
        return 0
    try:
        opt, masks = DosCmdLine.parse(args, switches)
    except DosCmdLine.Error, x:
        errln(str(x))
        return 2
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
            except IOError, x:
                errln('%s: "%s"' % (str(x), fspec))
                ioerror = True
    return 1 if foundsome or ioerror else 0


sys.exit(main(sys.argv[1:]))
