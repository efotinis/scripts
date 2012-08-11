"""Compare the files (and optionally their hashes) of two directories."""

import os
import sys
import hashlib
import argparse
import CommonTools


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
    # TODO: replace args.testmethod with an actual function
    if args.testmethod == 'n':
        pass
    elif args.testmethod == 'h':
        fn1 = os.path.join(root1, rel, name)
        fn2 = os.path.join(root2, rel, name)
        # TODO: checks hashes (or even bytes) in parallel
        if fsig(fn1) != fsig(fn2):
            print '**', os.path.join(rel, name)
            stats['mismatched_files'] += 1
            return
    elif args.testmethod == 'b':
        raise NotImplementedError('byte compare')
    else:
        assert False, 'invalid test method: "%s"' % args.testmethod
        
    if args.verbose:
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


def parse_args():
    parser = argparse.ArgumentParser(
        description='compare the files in two directories',
        add_help=False)

    add = parser.add_argument
    add('dir1', metavar='DIR1', help='first directory')
    add('dir2', metavar='DIR2', help='second directory')
    add('relpath', metavar='REL', nargs='?', help='common relative path')
    #add('-c', dest='matchcase', action='store_true', help='force case-sensitive comparisons')
    add('-t', dest='testmethod', choices='nhb', default='n',
        help='test method for matching files; n: by name (default), h: by MD5 hash, b: by bytes')
    #add('-b', dest='buflen', type=int, default=2*20, help='file I/O buffer size')
    add('-v', dest='verbose', action='store_true', help='verbose output; shows matched items')
    add('-?', action='help', help='this help')
    args = parser.parse_args()
    
    if args.relpath:
        args.dir1 = os.path.join(args.dir1, args.relpath)
        args.dir2 = os.path.join(args.dir2, args.relpath)
    del args.relpath
    
    if not os.path.isdir(args.dir1):
        parser.error('not a directory: "%s"' % args.dir1)
    if not os.path.isdir(args.dir2):
        parser.error('not a directory: "%s"' % args.dir2)

    args.dir1 = unicode(args.dir1)
    args.dir2 = unicode(args.dir2)
    
    return args


if __name__ == '__main__':

    args = parse_args()

    dir1, dir2 = args.dir1, args.dir2
    del args.dir1, args.dir2

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
