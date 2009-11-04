"""Convert directories to CBZ files.

For each subdirectory in the specified directory create a CBZ file
containing all its files (local only; no subdir recursion).

Generated CBZ files are uncompressed.
"""

import os, sys, zipfile
import CommonTools


def showhelp():
    print 'Convert subdirs to CBZ files.'
    print
    print '%s [root]' % (CommonTools.scriptname().upper(), )
    print
    print '  root  The directory to process. Defaults to the current one.'
    print
    print 'Only first level subdir files are stored (no recursion).'


def main(args):
    if '/?' in args:
        showhelp()
        raise SystemExit

    if len(args) > 1:
        raise SystemExit('too many arguments')

    root = args[0] if args else '.'
    if not os.path.isdir(root):
        raise SystemExit('invalid directory specified')
    
    for dirname in CommonTools.listdirs(root):
        print 'processing "%s" ...' % dirname
        zippath = os.path.join(root, dirname + '.cbz')
        z = zipfile.ZipFile(zippath, 'w', zipfile.ZIP_STORED)
        for s in CommonTools.listfiles(os.path.join(root, dirname)):
            z.write(os.path.join(root, dirname, s), s)
        z.close()


main(sys.argv[1:])
