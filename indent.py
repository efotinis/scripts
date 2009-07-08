"""Change source code indentation.

2007-04-13  EF  created
"""

import os, sys, re
import win32file, win32con
import DosCmdLine, CommonTools


# constants missing from win32con
FILE_READ_ATTRIBUTES = 0x0080
FILE_WRITE_ATTRIBUTES = 0x0100


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


def getFileTimes(fname):
    """Return 4-tuple of success and create/access/modify file times."""
    try:
        f = None
        f = win32file.CreateFile(fname, FILE_READ_ATTRIBUTES, 0, None,
                                 win32con.OPEN_EXISTING, 0, None)
        ret = win32file.GetFileTime(f)
    finally:
        if f:
            win32file.CloseHandle(f)
    return ret


def setFileTimes(fname, create, access, modify):
    """Set create/access/modify file times; any of them can be None."""
    try:
        f = None
        f = win32file.CreateFile(fname, FILE_WRITE_ATTRIBUTES, 0, None,
                                 win32con.OPEN_EXISTING, 0, None)
        win32file.SetFileTime(f, create, access, modify)
    finally:
        if f:
            win32file.CloseHandle(f)


def showhelp(switches):
    s = """\
Change source code indentation level.
Elias Fotinis 2007

%s oldsize newsize [input] [output]

%s

Exit codes: 0=ok, 1=error, 2=bad param"""
    name = CommonTools.scriptname().upper()
    table = '\n'.join(DosCmdLine.helptable(switches))
    print s % (name, table)


def main(args):
    Swch = DosCmdLine.Switch
    Flag = DosCmdLine.Flag
    Misc = lambda name, descr: DosCmdLine.Flag(name, None, descr)
    switches = (
##        Flag('W', 'readwhole',
##             'Read whole input file and close it before processing.'),
        Swch('T', 'tabsize',
             'Number of spaces to expand tabs into. Default is 8.',
             8, converter=int),
        Flag('R', 'replace',
             'Replace contents of input file, preserving timestamps. '
             'Input file name is mandatory, output is forbidden.'),
        Misc(('oldsize', 'newsize'), 'Old/new size of indentation.'),
        Misc(('input', 'output'), 'Input/output files; omit or use "" to specify STDIN/STDOUT.'),
    )
    if '/?' in args:
        showhelp(switches)
        return EXIT_OK
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if not 2 <= len(params) <= 4:
            raise DosCmdLine.Error('only 2 to 4 params are allowed')
        if opt.replace and len(params) != 3:
            raise DosCmdLine.Error('exactly 3 params are required with \R')
        params += [''] * (4 - len(params))
        try:
            opt.oldsize = int(params[0])
            opt.newsize = int(params[1])
            del params[:2]
        except ValueError, x:
            raise DosCmdLine.Error('invalid level number; ' + str(x))
        if opt.oldsize <= 0 or opt.newsize <= 0:
            raise DosCmdLine.Error('indentation levels must be >0')
    except DosCmdLine.Error, x:
        CommonTools.errln(str(x))
        return EXIT_BAD_PARAM

    flags = {
        'EMPTY_LINES':'pad',
        'CPP_SMART_PREPROC':True,
        'CPP_DTOR_DEF_ALIGN':True,
        'TAB_SIZE':opt.tabsize,
    }
    indent = IndentSession(opt.oldsize , opt.newsize, flags)

    if opt.replace:
        timestamps = getFileTimes(params[0])[1:]
        params[1] = params[0] + '$'

    infile = CommonTools.InFile(params[0])
    outfile = CommonTools.OutFile(params[1])
    for s in infile:
        s = s.rstrip('\n')
        s = indent.process(s)
        outfile.write(s + '\n')
    infile.close()
    outfile.close()

    if opt.replace:
        setFileTimes(params[1], *timestamps)
        os.unlink(params[0])
        os.rename(params[1], params[0])


sys.exit(main(sys.argv[1:]))
