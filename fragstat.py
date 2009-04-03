# 2007.04.04  created
# 2007.09.24  utilized DosCmdLine; added some comments

import os
import re
import sys
import win32api
import win32file
import win32con
import DosCmdLine


def getDriveRoots(types=None):
    a = win32api.GetLogicalDriveStrings()[:-1].split('\0')
    if types is None:
        return a
    elif isinstance(types, int):
        types = (types,)
    return [s for s in a if win32file.GetDriveType(s) in types]


def getFileContents(fpath):
    """Return the whole contents of a file, or '' on error."""
    ret = ''
    f = None
    try:
        f = file(fpath)
        ret = f.read()
    finally:
        if f:
            f.close()
    return ret


def run(cmd):
    """Run a cmd and return exit code and stdout/stderr strings.

    STDOUT and STDERR are captured by redirection to temp files.
    If the cmd interpreter cannot run the cmd, the exit code is set to -1.
    """
    tmpDir = win32api.GetTempPath() or '.'
    cout = win32api.GetTempFileName(tmpDir, '')[0]
    cerr = win32api.GetTempFileName(tmpDir, '')[0]
    try:
        redir = ' > "%s" 2> "%s"' % (cout, cerr)
        exitCode = os.system(cmd + redir)
    except:
        exitCode = 256
    finally:
        s1 = getFileContents(cout)
        s2 = getFileContents(cerr)
        os.unlink(cout)
        os.unlink(cerr)
        return (exitCode, s1, s2)
    

def parseDefragReport(s):
    """Get DEFRAG's analysis results and return the juicy parts."""
    REPORT_RX = re.compile(
        r'^'
        r'(?P<title>.*)\n'
        r'(?P<copyright>Copyright.*)\n\n'
        r'Analysis Report[ \t]*\n'
            r'\s+(?P<size>.+) Total,'
            r'\s+(?P<free>.+) \((?P<freePc>.+)\) Free,'
            r'\s+(?P<fragm>.+) Fragmented \((?P<fileFragm>.+) file fragmentation\)\n\n'
        r'(?P<recommend>.*?)[ \t]*\n'
        r'$')
    recommendations = {
        'You do not need to defragment this volume.':False,
        'You should defragment this volume.':True}
    mo = re.match(REPORT_RX, s)
    if not mo:
        raise Exception('Could not parse defrag report.')
    return (mo.group('size'), mo.group('free'), mo.group('freePc'),
            mo.group('fragm'), mo.group('fileFragm'),
            recommendations.get(mo.group('recommend')))
    

def runAnalysis():
    """Print a table of DEFRAG analysis results for each fixed drive."""
    error = False
    header = 'Drive ______Size ______Free_____ Frgm_file needDefrag?'
    #print header.replace('_', ' ')
    print header
    for root in getDriveRoots(win32con.DRIVE_FIXED):
        exitCode, cout, cerr = run('defrag ' + root + ' -a')
        print '%-5s' % root,
        if exitCode == -1:
            print 'Could not run DEFRAG.'
            error = True
        elif exitCode != 0:
            print cerr.strip('\n').split('\n')[0]  # first non-empty line
            error = True
        else:
            try:
                #size, free, freePc, fragm, fileFragm, recm = parseDefragReport(cout)
                a = parseDefragReport(cout)
                a = a[:-1] + ({True:'Yes', False:'No', None:'???'}[a[-1]],)
                print '%10s %10s %4s %4s %4s %s' % a
            except Exception, x:
                print x
                error = True
    return not error


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def showhelp(switches):
    print """\
Display DEFRAG analysis for all fixed drives.
Elias Fotinis 2007

FRAGSTAT.PY
"""
    DosCmdLine.showlist(switches)
    print """
Exit codes: 0=ok, 1=error, 2=bad params."""


def main(args):
    switches = (
        DosCmdLine.Flag('?', 'help', None),
    )
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if params:
            raise DosCmdLine.Error('no params allowed')
    except DosCmdLine.Error, x:
        errln(str(x))
        return 2
    if opt.help:
        showhelp(switches)
        return 0
    return 0 if runAnalysis() else 1


sys.exit(main(sys.argv[1:]))
