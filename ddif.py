"""Compare the files (and optionally their hashes/bytes) of two directories."""

import os
import sys
import hashlib
import argparse
import CommonTools


IO_BUFLEN = 2 ** 20


if os.name == 'posix':
    CASE_SENSITIVE_PLATFORM_PATHS = True
elif os.name == 'nt':
    CASE_SENSITIVE_PLATFORM_PATHS = False
else:
    CASE_SENSITIVE_PLATFORM_PATHS = None  # will err if user selects it


def merged(a, b, case_sens):
    """Merge two lists.

    Generates each item and a character. The character shows in which list
    the item was found: '<' (first), '>' (second), or '=' (both).
    """
    if case_sens:
        sort_key = lambda s: s
        item_cmp = lambda s1, s2: cmp(s1, s2)
    else:
        sort_key = lambda s: s.lower()
        item_cmp = lambda s1, s2: cmp(s1.lower(), s2.lower())

    a = sorted(a, key=sort_key)
    b = sorted(b, key=sort_key)

    while a or b:
        if not a:
            yield b.pop(0), '>'
        elif not b:
            yield a.pop(0), '<'
        else:
            order = item_cmp(a[0], b[0])
            if order < 0:
                yield a.pop(0), '<'
            elif order > 0:
                yield b.pop(0), '>'
            else:
                b.pop(0)
                yield a.pop(0), '='


def compare_file_hashes(path1, path2):
    """Compare two files using MD5 hashes.

    Returns False as soon as a difference is detected, otherwise True.
    """
    if os.path.getsize(path1) != os.path.getsize(path2):
        return False
    hash1, hash2 = hashlib.md5(), hashlib.md5()
    with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
        while True:
            s1, s2 = f1.read(IO_BUFLEN), f2.read(IO_BUFLEN)
            if len(s1) != len(s2):
                # size mismatch
                return False
            elif not s1:
                # both files exhausted
                return True
            else:
                hash1.update(s1)
                hash2.update(s2)
                if hash1.digest() != hash2.digest():
                    return False


def compare_file_bytes(path1, path2):
    """Compare two files via byte-by-byte testing.
    
    Returns False as soon as a difference is detected, otherwise True.
    """
    if os.path.getsize(path1) != os.path.getsize(path2):
        return False
    with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
        while True:
            s1, s2 = f1.read(IO_BUFLEN), f2.read(IO_BUFLEN)
            if len(s1) != len(s2):
                # size mismatch
                return False
            elif not s1:
                # both files exhausted
                return True
            else:
                if s1 != s2:
                    return False
        

def compare_dirs(root1, root2, rel, stats, args):
    """Compare two dirs."""

    merged_names = merged(
        os.listdir(os.path.join(root1, rel)),
        os.listdir(os.path.join(root2, rel)),
        args.case_sens)

    for name, where in merged_names:
        if where == '<':
            isdir = os.path.isdir(os.path.join(root1, rel, name))
            if isdir:
                list_unmatched_dir(root1, os.path.join(rel, name), stats, 'only_in_a', '1 ')
            else:
                CommonTools.conout('1 ', os.path.join(rel, name))
                stats['only_in_a'] += 1
        elif where == '>':
            isdir = os.path.isdir(os.path.join(root2, rel, name))
            if isdir:
                list_unmatched_dir(root2, os.path.join(rel, name), stats, 'only_in_b', ' 2')
            else:
                CommonTools.conout(' 2', os.path.join(rel, name))
                stats['only_in_b'] += 1
        else:
            isdir1 = os.path.isdir(os.path.join(root1, rel, name))
            isdir2 = os.path.isdir(os.path.join(root2, rel, name))
            if isdir1 and isdir2:
                compare_dirs(root1, root2, os.path.join(rel, name), stats, args)
            elif not isdir1 and not isdir2:
                path1 = os.path.join(root1, rel, name)
                path2 = os.path.join(root2, rel, name)
                if args.content_matcher(path1, path2):
                    if args.verbose:
                        CommonTools.conout('==', os.path.join(rel, name))
                    stats['matched_files'] += 1
                else:
                    CommonTools.conout('**', os.path.join(rel, name))
                    stats['mismatched_files'] += 1
            else:  # file <-> dir
                if isdir1:
                    list_unmatched_dir(root1, os.path.join(rel, name), stats, 'only_in_a', '1 ')
                    CommonTools.conout(' 2', os.path.join(rel, name))
                    stats['only_in_b'] += 1
                else:
                    CommonTools.conout('1 ', os.path.join(rel, name))
                    stats['only_in_a'] += 1
                    list_unmatched_dir(root2, os.path.join(rel, name), stats, 'only_in_b', ' 2')


def list_unmatched_dir(root, rel, stats, stats_key, prefix):
    """Recursively print all files under an unmatched directory."""
    for name in os.listdir(os.path.join(root, rel)):
        isdir = os.path.isdir(os.path.join(root, rel, name))
        if isdir:
            list_unmatched_dir(root, os.path.join(rel, name), stats, stats_key, prefix)
        else:
            CommonTools.conout(prefix, os.path.join(rel, name))
            stats[stats_key] += 1


def parse_args():
    parser = argparse.ArgumentParser(
        description='compare the files in two directories')

    add = parser.add_argument
    add('dir1', metavar='DIR1', help='first directory')
    add('dir2', metavar='DIR2', help='second directory')
    add('relpath', metavar='REL', nargs='?', help='common relative path')
    add('--case-sens', choices='mip', default='p',
        help='name case comparisons; m: match, i: ignore, p: platform specific (default)')
    add('-c', dest='content_matcher', choices='nhb', default='n',
        help='file contents comparison; n: none (default), h: MD5 hash, b: bytes')
    #add('-b', dest='buflen', type=int, default=2*20, help='file I/O buffer size')
    add('-v', dest='verbose', action='store_true', help='verbose output; shows matched items')
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

    if args.case_sens == 'm':
        args.case_sens = True
    elif args.case_sens == 'i':
        args.case_sens = False
    else:
        if CASE_SENSITIVE_PLATFORM_PATHS is None:
            parser.error('current platforn path case sensitivity is unknown')
        args.case_sens = CASE_SENSITIVE_PLATFORM_PATHS

    args.content_matcher = {
        'n': lambda s1, s2: True,
        'h': compare_file_hashes,
        'b': compare_file_bytes,
    } [args.content_matcher]

    return args


if __name__ == '__main__':

    args = parse_args()
##    print args
##    sys.exit()

    dir1, dir2 = args.dir1, args.dir2
    del args.dir1, args.dir2

    stats = {'only_in_a':0, 'only_in_b':0, 
             'mismatched_files':0, 'matched_files':0}
    try:
        compare_dirs(dir1, dir2, '', stats, args)
        print
        print 'Totals:'
        print '  (==)    matched:', stats['matched_files']
        print '  (**) mismatched:', stats['mismatched_files']
        print '  (1 )  only in 1:', stats['only_in_a']
        print '  ( 2)  only in 2:', stats['only_in_b']
    except KeyboardInterrupt:
        sys.exit('cancelled by user')
