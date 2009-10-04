"""Replace tabs with spaces."""

import os
import sys
import optparse

import CommonTools


def parse_cmdline():
    op = optparse.OptionParser(
        usage='%prog [options] [INPUT] [OUTPUT]',
        description='Replace tabs with spaces.',
        epilog='INPUT/OUTPUT default to STDIN/STDOUT if omitted or set to "".',
        add_help_option=False)
    add = op.add_option
    add('-s', dest='tabsize', type='int', default=8, 
        help='Tab size. Default is 8.')
    add('-b', dest='onlybeg', action='store_true', 
        help='Process tabs only at the beginning of each line.')
    add('-w', dest='readwhole', action='store_true', 
        help='Read whole input file and close it before processing. '
        'Can be used to replace a file in-place.')
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)
    return op.parse_args()


if __name__ == '__main__':
    try:
        opt, args = parse_cmdline()
        if len(args) > 2:
            raise optparse.OptParseError('at most 2 params are allowed')
        while len(args) < 2:
            args.append('')
    except optparse.OptParseError as err:
        CommonTools.exiterror(str(err), 2)
        
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
        
    try:
        infile = CommonTools.InFile(args[0])
        outfile = CommonTools.OutFile(args[1])
        if opt.readwhole:
            a = infile.readlines()
            infile.close()
            for s in a:
                outfile.write(expandfunc(s, opt.tabsize))
        else:
            for s in infile:
                outfile.write(expandfunc(s, opt.tabsize))
    except IOError as err:
        CommonTools.exiterror(str(err))
