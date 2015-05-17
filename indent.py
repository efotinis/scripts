"""Change source code indentation."""

import os
import sys
import re
import argparse

import win32file
import win32con

import efutil
import wintime


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_PARAM = 2

DTOR_DEFINITION_RX = re.compile(r'^\s+~\w*\(\)')


def count_lead(s, chars):
    """Return number of leading characters."""
    count = 0
    for c in s:
        if c not in chars:
            break
        count += 1
    return count
    

def reindent(s, oldsize, newsize, lastlevel, flags):
    """Indent a line and return it along with the new level."""

    # EMPTY_LINES = 'ignore' / 'trim' / 'pad'
    # CPP_SMART_PREPROC = True / False
    # CPP_DTOR_DEF_ALIGN = True / False

    s = s.expandtabs(flags['TAB_SIZE'])
    leadspace = count_lead(s, ' ')

    if leadspace == len(s):
        # empty line
        if flags['EMPTY_LINES'] == 'trim':
            return '', lastlevel
        elif flags['EMPTY_LINES'] == 'pad':
            # give empty lines the same indent as the previous line
            # (wastes a bit of space, but it's better with editors
            # that don't support virtual space)
            return lastlevel * newsize * ' ', lastlevel
        else:
            return s, lastlevel

    if flags['CPP_SMART_PREPROC'] and s[0] == '#':
        # a preproc directive on col 0; return as is and keep last level
        return s, lastlevel

    # usually dtor defs are one space short, to line up the names
    is_dtordef = False
    if flags['CPP_DTOR_DEF_ALIGN']:
        is_dtordef = bool(DTOR_DEFINITION_RX.match(s))
        if is_dtordef:
            leadspace += 1

    # calc integral indentation level
    newlevel = int(leadspace / oldsize)

    # indentation should never increase more than one level
    if newlevel > lastlevel + 1:
        newlevel = lastlevel + 1

    # left-over spaces are probably used to line up multi-line statements
    restOfIndent = leadspace - newlevel * oldsize

    newSpaceCnt = newlevel * newsize + restOfIndent
    if is_dtordef:
        leadspace -= 1
        newSpaceCnt -= 1
        
    return ' ' * newSpaceCnt + s[leadspace:], newlevel


class IndentSession:
    def __init__(self, oldsize, newsize, flags):
        self.oldsize = oldsize
        self.newsize = newsize
        self.lastlevel = 0
        self.flags = flags.copy()
    def process(self, s):
        s, self.lastlevel = reindent(s, self.oldsize, self.newsize,
                                     self.lastlevel, self.flags)
        return s
        

##
### TODO: accept CLI switches
##INDENT_SIZE_OLD = 2
##INDENT_SIZE_NEW = 4
##TABS_ARE_FATAL = False
##TAB_SIZE = 2
##WRITE_FILE_AND_BACKUP = True
##
##
### TODO: these apply only to C++ files
##DTOR_DEFINITION_RX = re.compile(r'^\s+~\w*\(\)')
##SMART_HANDLE_CPP_PREPROC = True
##
##
##
##def convertTabsToSpaces(s, tabSize):
##    i = 0
##    while True:
##        i = s.find('\t', i)
##        if i == -1:
##            break
##        width = (i/tabSize + 1)*tabSize - i
##        s = s[:i] + ' '*width + s[i+1:]
##        i += width
##    return s
##
##
##def processLines(a):
##    """Process an array of file lines."""
##    ret = []
##    lastlevel = 0
##
##    for s in a:
##        hasEol = s.endswith('\n')
##        if hasEol:
##            s = s[:-1]
##        s, lastlevel = reindent(s, INDENT_SIZE_OLD, INDENT_SIZE_NEW, lastlevel)
##        if hasEol:
##            s += '\n'
##        ret.append(s)
##    return ret
##
##
##def replaceFileContentsAndBackup(fname, lines):
##    timeInfo = getFileTimes(fname)
##    if not timeInfo[0]:
##        timeInfo = timeInfo[0] + [None]*3
##
##    bakName = buildBakName(fname)
##    os.rename(fname, bakName)
##
##    with file(fname, 'w') as f:
##        for s in lines:
##            f.write(s + '\n')
##    setFileTimes(fname, timeInfo[1], None, timeInfo[3])
##
##
##def buildBakName(fname):
##    s, ext = os.path.splitext(fname)
##    i = 0
##    while True:
##        newName = '%s.%d%s' % (s, i, ext)
##        if not os.path.exists(newName):
##            return newName
##        i += 1
##
##
##def processFile(fname):
##    """Process a file and print result to STDOUT or write file."""
##
##    if TABS_ARE_FATAL:
##        tabLines = []
##        
##    with file(fname) as f:
##        lines = []
##        for i, s in enumerate(f):
##            s = s.rstrip('\n')
##            if '\t' in s:
##                if TABS_ARE_FATAL:
##                    tabLines += [str(i+1)]
##                else:
##                    s = convertTabsToSpaces(s, TAB_SIZE)
##            lines.append(s)
##
##    if TABS_ARE_FATAL and tabLines:
##        print 'ERROR: TABs detected in "' + fname + '" at lines: ' + ','.join(tabLines)
##        return
##
##    newLines = processLines(lines)
##    if WRITE_FILE_AND_BACKUP:
##        #if newLines <> lines:
##        replaceFileContentsAndBackup(fname, newLines)
##    else:
##        for line in newLines:
##            print line
##
##
##def errln(s):
##    sys.stderr.write('ERROR: ' + s + '\n')
##
##    
##def main(args):
##
##    if len(args) > 2:
##        errln('at most 2 parameters are allowed')
##        return ERROR_BAD_PARAMS
##    while len(args) < 2:
##        args += ['']
##
##    try:
##        infile = file(args[0]) if args[0] else sys.stdin
##        lines = infile.readlines()
##        if infile is not sys.stdin:
##            infile.close()
##    except IOError, x:
##        errln('could not read file; ' + str(x))
##        return EXIT_ERROR
##
##
####    if not processFile(s):
####        return EXIT_ERROR
##
##
##    try:
##        outfile = file(args[1], 'w') if args[1] else sys.stdout
##        outfile.writelines(lines)
##        if outfile is not sys.stdout:
##            outfile.close()
##    except IOError, x:
##        errln('could not write file; ' + str(x))
##        return EXIT_ERROR
##
##    return EXIT_OK


def parse_args():
    ap = argparse.ArgumentParser(
        description='change source code indentation level',
        add_help=False)

    add = ap.add_argument

    add('-t', dest='tabsize', type=int, default=8,
        help='tab size; default: %(default)s')
    add('-r', dest='replace', action='store_true',
        help='replace file with result, preserving timestamps; '
             'exactly 1 file parameter is required for both input and output')
    add('oldsize', type=int,
        help='old indentation size')
    add('newsize', type=int,
        help='new indentation size')
    add('input', nargs='?', default='',
        help='input file; omit or use "" to specify STDIN')
    add('output', nargs='?', default='',
        help='output file; omit or use "" to specify STDOUT')
    add('-?', action='help',
        help='this help')

    args = ap.parse_args()

    if args.replace and (not args.input or args.output):
        ap.error('-r requires exactly 1 file param')
    if args.oldsize <= 0 or args.newsize <= 0:
        ap.error('indentation size must be >0')
    
    return args


if __name__ == '__main__':
    args = parse_args()
    
    flags = {
        'EMPTY_LINES':'pad',
        'CPP_SMART_PREPROC':True,
        'CPP_DTOR_DEF_ALIGN':True,
        'TAB_SIZE':args.tabsize,
    }
    indent = IndentSession(args.oldsize , args.newsize, flags)

    if args.replace:
        timestamps = wintime.get_file_time(args.input)[1:]
        args.output = args.input + '$'

    infile = efutil.InFile(args.input)
    outfile = efutil.OutFile(args.output)
    for s in infile:
        s = s.rstrip('\n')
        s = indent.process(s)
        outfile.write(s + '\n')
    infile.close()
    outfile.close()

    if args.replace:
        wintime.set_file_time(args.output, *timestamps)
        os.unlink(args.input)
        os.rename(args.output, args.input)
