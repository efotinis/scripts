"""Compare the files (and optionally their hashes) of two directories."""

import os
import sys
import hashlib
import getopt
import CommonTools


SHOW_MATCHED_FILES = False
COMPARE_FILE_HASHES = False


def merged(a, b):
    """Merge two sorted lists.

    Generates each item and a character. The character shows in which list
    the item was found: '<' (first), '>' (second), or '=' (both).
    """
    a, b = a[:], b[:]
    while a or b:
        if not a:
            yield b.pop(0), '>'
        elif not b:
            yield a.pop(0), '<'
        else:
            if a[0] == b[0]:
                b.pop(0)
                yield a.pop(0), '='
            elif a[0] < b[0]:
                yield a.pop(0), '<'
            else:
                yield b.pop(0), '>'


def fsig(fn, buflen=2**20):
    hash = hashlib.md5()
    with open(fn, 'rb') as f:
        while True:
            s = f.read(buflen)
            if not s:
                break
            hash.update(s)
    return hash.digest()


def compare_files(root1, root2, rel, name, stats):
    if COMPARE_FILE_HASHES:
        fn1 = os.path.join(root1, rel, name)
        fn2 = os.path.join(root2, rel, name)
        if fsig(fn1) != fsig(fn2):
            print '**', os.path.join(rel, name)
            stats['mismatched_files'] += 1
            return
    if SHOW_MATCHED_FILES:
        print '==', os.path.join(rel, name)
    stats['matched_files'] += 1
        

def compare_dirs(root1, root2, rel, stats):
    a1 = sorted(os.path.normcase(s) for s in os.listdir(os.path.join(root1, rel)))
    a2 = sorted(os.path.normcase(s) for s in os.listdir(os.path.join(root2, rel)))
    for name, where in merged(a1, a2):
        if where in '<':
            print '1 ', os.path.join(rel, name)
            stats['only_in_a'] += 1
        elif where in '>':
            print ' 2', os.path.join(rel, name)
            stats['only_in_b'] += 1
        else:
            isdir1 = os.path.isdir(os.path.join(root1, rel, name))
            isdir2 = os.path.isdir(os.path.join(root2, rel, name))
            if isdir1 and isdir2:
                compare_dirs(root1, root2, os.path.join(rel, name), stats)
            elif not isdir1 and not isdir2:
                compare_files(root1, root2, rel, name, stats)
            else:
                print '!!', os.path.join(rel, name)
                stats['file_dir_mismatches'] += 1


HELP_TEXT = '''
Compare two directories.

usage: %s [options] DIR1 DIR2 [RELPATH]

  DIR1,DIR2  The directories to compare.
  RELPATH    Optional relative path.
  -m         Display matched files (not shown by default).
  -h         Hash and compare file contents.
  -?         This help.
'''[1:-1] % CommonTools.scriptname()


def parse_cmdline():
    global SHOW_MATCHED_FILES
    global COMPARE_FILE_HASHES

    opts, args = getopt.gnu_getopt(sys.argv[1:], 'mh?')
    opts = dict(opts)
    if '-?' in opts:
        print HELP_TEXT
        sys.exit()

    if '-m' in opts:
        SHOW_MATCHED_FILES = True
    if '-h' in opts:
        COMPARE_FILE_HASHES = True

    if len(args) == 2:
        dir1, dir2 = map(unicode, args)
        return dir1, dir2
    elif len(args) == 3:
        dir1, dir2, rel = map(unicode, args)
        dir1 = os.path.join(dir1, rel)
        dir2 = os.path.join(dir2, rel)
        return dir1, dir2
    else:
        sys.exit('2 or 3 parameters required')


if __name__ == '__main__':
    dir1, dir2 = parse_cmdline()
    stats = {'only_in_a':0, 'only_in_b':0, 'file_dir_mismatches':0,
             'mismatched_files':0, 'matched_files':0}
    try:
        compare_dirs(dir1, dir2, '', stats)
        print
        print '            only in 1:', stats['only_in_a']
        print '            only in 2:', stats['only_in_b']
        print '  file/dir mismatches:', stats['file_dir_mismatches']
        print '     mismatched files:', stats['mismatched_files']
        print '        matched files:', stats['matched_files']
    except KeyboardInterrupt:
        sys.exit('cancelled by user')
