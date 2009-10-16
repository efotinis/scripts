import os
import sys

import DosCmdLine


def get_envlist(s):
    """Split and return a PATH-like (';'-delimited) env var; [] on error."""
    try:
        return os.environ[s].split(';')
    except KeyError:
        return []


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def strimatch(s1, s2):
    return s1.lower() == s2.lower()


def locate_file(fname, exts, paths, opt):
    """Check a file and return whether it was located."""
    found = False
    if not opt.bareout:
        print fname
    for cur_path in paths:
        for cur_ext in exts:
            s = os.path.join(cur_path, fname + cur_ext)
            if os.path.isfile(s):
                if not opt.bareout:
                    s = "  " + s
                print s
                found = True
                if not opt.findall:
                    return found
    if not found and not opt.bareout:
        print "  <not found>"
    return found


def locate(files, opt):
    """Check a list of files and return true if at least one was located."""
    # insert '' to initially check without adding an extension
    exts = [''] + get_envlist('PATHEXT')
    # insert the CWD to initially look in the current dir
    paths = [os.getcwd()] + get_envlist('PATH')
    found = False
    for s in files:
        if locate_file(s, exts, paths, opt):
            found = True
    return found


def showHelp(switches):
    print """\
Locates executable files, using the PATH and PATHEXT environment variables.
Elias Fotinis 2005-2007

LOCATE.PY [/A] [/B] files
"""
    DosCmdLine.showlist(switches)
    print """
ERRORLEVEL is set to 0 if at least one instance of any of the specified files
is found, or 1 otherwise. It's set to 2 if the parameters are wrong."""


def main(args):
    Flag = DosCmdLine.Flag
    switches = [
        Flag('?', 'help', None),
        Flag('A', 'findall',
             'Locate all occurences, instead of just the first one.'),
        Flag('B', 'bareout',
             'Print only found file paths. By default, the specified files '
             'on the command line are printed, followed by the found path '
             'names or a not-found message.'),
        Flag('files', None,
             'The files to locate. Directories and wildcards are not allowed.'),
    ]
    try:
        opt, files = DosCmdLine.parse(args, switches)
    except DosCmdLine.Error, x:
        errln(str(x))
        return 2
    if opt.help:
        showHelp(switches)
        return 0
    return 0 if locate(files, opt) else 1


sys.exit(main(sys.argv[1:]))
