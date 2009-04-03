"""Replace tabs with spaces.

2007.11.23 EF: created
"""

import os, sys
import DosCmdLine, CommonTools

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_PARAM = 2


def showhelp(switches):
    s = """\
Replace tabs with spaces.
Elias Fotinis 2007

%s [/S:size] [input] [output]

%s

Exit codes: 0=ok, 1=error, 2=bad param"""
    name = CommonTools.scriptname().upper()
    table = '\n'.join(DosCmdLine.helptable(switches))
    print s % (name, table)


def main(args):

    Swtc = DosCmdLine.Switch
    Flag = DosCmdLine.Flag
    Misc = lambda name, descr: DosCmdLine.Flag(name, None, descr)
    switches = (
        Swtc('S', 'tabsize',
             'Tab size. Default is 8.',
             8, converter=int),
        Flag('B', 'onlybeg',
             'Process tabs only at the beginning of each line.'),
        Flag('W', 'readwhole',
             'Read whole input file and close it before processing.'),
        Misc(('input', 'output'), 'Input/output files; omit or use "" to specify STDIN/STDOUT.'),
    )
    if '/?' in args:
        showhelp(switches)
        return EXIT_OK
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if len(params) > 2:
            raise DosCmdLine.Error('at most 2 params are allowed')
        params += [''] * (2 - len(params))
    except DosCmdLine.Error, x:
        CommonTools.errln(str(x))
        return EXIT_BAD_PARAM

    if opt.onlybeg:
        def expandfunc(s, tabsize):
            # count leading tabs
            count = 0
            for c in s:
                if c != '\t':
                    break
                count += 1
            return ' ' * max(0, tabsize) * count + s[count:]
    else:
        import string
        expandfunc = string.expandtabs
        
    infile = CommonTools.InFile(params[0])
    outfile = CommonTools.OutFile(params[1])
    if opt.readwhole:
        a = infile.readlines()
        infile.close()
        for s in a:
            outfile.write(expandfunc(s, opt.tabsize))
    else:
        for s in infile:
            outfile.write(expandfunc(s, opt.tabsize))


sys.exit(main(sys.argv[1:]))
