"""Show fragmentation statistics of all fixed drives in the system."""

import os
import re
import sys
import optparse
import subprocess

import win32con

import diskutil


# TODO: add Vista report parsing support (only works on XP now)


def readfile(name, mode='r'):
    """Read a whole file; return None on error."""
    try:
        with open(name, mode) as f:
            return f.read()
    except IOError:
        return None


def run(cmd):
    """Run a shell command and return the exit code and stdout/stderr strings."""
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, strerr = p.communicate()
    return p.returncode, stdout, strerr
    

def parseDefragReport(s):
    """Get DEFRAG's analysis results and return the juicy parts."""
    # TODO: return a namedtuple
    # TODO: use verbose regex pattern
    # NOTE: free percentage is truncated to integer; better ignore the DEFRAG value
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
    return (mo.group('size'), mo.group('free'), mo.group('freePc'), mo.group('fragm'),
            mo.group('fileFragm'), recommendations.get(mo.group('recommend'))) if mo else None
    

def runAnalysis():
    """Print a table of DEFRAG analysis results for each fixed drive."""
    error = False
    header = 'Drive ______Size ______Free_____ Frgm_file needDefrag?'
    #print header.replace('_', ' ')
    print header
    for drive in diskutil.logical_drives(win32con.DRIVE_FIXED):
        exitCode, cout, cerr = run('defrag %c: -a' % drive)
        cout = cout or ''
        cerr = cerr or ''
        print '%-4c:' % drive,
        if exitCode == -1:
            print 'Could not run DEFRAG.'
            error = True
        elif exitCode != 0:
            print cerr.strip('\n').split('\n')[0]  # first non-empty line
            error = True
        else:
            a = parseDefragReport(cout)
            if a:
                a = a[:-1] + ({True:'Yes', False:'No', None:'???'}[a[-1]],)
                print '%10s %10s %4s %4s %4s %s' % a
            else:
                print 'Could not parse defrag report.'
                error = True
    return not error


def getopt():
    op = optparse.OptionParser(
        usage='%prog',
        description='Display DEFRAG analysis for all fixed drives.',
        epilog=None,
        add_help_option=False)
    add = op.add_option
    add('-?', action='help',
        help=optparse.SUPPRESS_HELP)
    opt, args = op.parse_args()
    if args:
        op.error('no params allowed')
    return opt, args


if __name__ == '__main__':
    opt, args = getopt()
    if sys.getwindowsversion()[:1] != (5, 1):
        sys.exit('only Windows XP is supported at the moment')
    if not runAnalysis():
        sys.exit(1)
