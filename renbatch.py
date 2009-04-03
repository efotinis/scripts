"""Rename multiple files by editing their names in a text file.

First generate a file listing. It looks like this:

    C:\some dir\                <-  start of dir; path ends with '\'
    file1.ext                   <-\ list of file names; one per line
    file2.ext
                                <-  blank; sep (ignored)
    C:\some other dir\
    fileX.ext
    fileY.ext

Then copy this file, edit the file names and commit the changes to the
original listing.

NOTE: Do not add/delete any lines. Only modify any file names needed.

EF 2007.12.29

"""

import os, re, sys


def parse(fname):
    """Read mapping of dir paths to list of file names."""
    ret = {}
    cur = None
    for s in open(fname):
        s = s.rstrip('\n')
        if not s:
            continue
        elif s.endswith('\\'):
            ret[s] = cur = []
        else:
            cur += [s]
    return ret


def rename(dpath, src, dst):
    """Rename a file, adding a unique index if needed."""
    i = 0
    s = os.path.join(dpath, dst)
    base, ext = os.path.splitext(dst)
    while os.path.exists(s):
        i += 1
        s = os.path.join(dpath, '%s %d%s' % (base, i, ext))
    os.rename(os.path.join(dpath, src), s)


def errln(s):
    sys.stderr.write('ERROR: ' + s + '\n')


def showhelp():
    script = os.path.splitext(os.path.basename(sys.argv[0]))[0].upper()
    print """\
Rename multiple files by editing their names in a text file.

Generate a file listing:
%(script)s  L  dir outfile

  dir      The directory to list (recursively).
  outfile  The output file.

Perform the renames:
%(script)s  R  srclist dstlist

  srclist  The original listing generated.
  dstlist  The modified listing.

Conflicts are resolved by adding a unique number before the file extension.
Exit codes: 0=ok, 1=error, 2=bad param\
""" % locals()


class BadParam(Exception):
    def __init__(self, s):
        Exception.__init__(self, s)


def doList(args):
    """Perform list operation."""
    if len(args) != 2:
        raise BadParam('2 params are required')
    # recursively write a dir line followed by a list of files
    f = open(args[1], 'w')
    for parent, dirs, files in os.walk(args[0]):
        print >>f, parent + '\\'
        for s in files:
            print >>f, s
        print >>f
    f.close()


def doRename(args):
    """Perform rename commit operation."""
    if len(args) != 2:
        raise BadParam('2 params are required')
    src = parse(args[0])
    dst = parse(args[1])
    if src.keys() != dst.keys():
        raise Exception('src/dst listing dirs do not match')

    allok = True
    numrenamed = 0
    for dpath in src.keys():
        srcfiles, dstfiles = src[dpath], dst[dpath]
        if len(srcfiles) != len(dstfiles):
            errln('src/dst files of dir "%s" do not match' % dpath)
            allok = False
            continue
        for srcname, dstname in zip(srcfiles, dstfiles):
            if srcname != dstname:
                rename(dpath, srcname, dstname)
                numrenamed += 1
    print 'files renamed:', numrenamed
    return allok


def main(args):
    """Launch operation (or help) and return exit code."""
    try:
        if not args or '/?' in args or '-?' in args:
            showhelp()
            return 0
        elif args[0].upper() == 'L':
            doList(args[1:])
            return 0
        elif args[0].upper() == 'R':
            return 0 if doRename(args[1:]) else 1
        else:
            raise BadParam('invalid operation')
    except BadParam, x:
        errln(str(x))
        return 2
    except Exception, x:
        errln(str(x))
        return 1


sys.exit(main(sys.argv[1:]))
