"""Copy files and calculate hashes at the same time."""

import argparse
import collections
import glob
import hashlib
import os
import sys


def parse_args():
    p = argparse.ArgumentParser(
        description='copy files and generate hash of source contents; '
        'the hash is a .TXT file named after the hash type with a numeric '
        'suffix to avoid overwriting existing files--each line consists of '
        'the hash value and the file basename, separated by a space'
    )

    p.add_argument('input', nargs='*',
        help='source file paths (recursive glob); if omitted, source paths '
        'are read from STDIN; NOTE: this uses *nix-style pattern matching, '
        'where dot-files are ignored and hidden files are included'
    )
    p.add_argument('-d', dest='destination', required=True,
        help='output directory; will be created if needed'
    )
    p.add_argument('-t', dest='hashtype', default='sha256',
        help='hash function; default: %(default)s'
    )
    #p.add_argument('-o', dest='hashpath',
    #    help='hash function; default: %(default)s'
    #)
    p.add_argument('-b', dest='bufsize', type=int, default=2**20,
        help='buffer size; default: %(default)s'
    )

    args = p.parse_args()

    try:
        os.makedirs(args.destination, exist_ok=True)
    except FileExistsError:
        p.error('output directory path exists and is a file')
    except OSError as x:
        p.error('could not create output directory; ' + str(x))

    if not args.input:
        args.input = [s.rstrip('\n') for s in sys.stdin.readlines()]

    return args


def expand_globs(patterns):
    """Expand globs recursively, select files only and print warning when nothing matches."""
    for p in patterns:
        a = [s for s in glob.glob(p, recursive=True) if os.path.isfile(s)]
        if a:
            yield from a
        else:
            print(f'WARNING: file not found: {p}')


def prune_duplicates(paths):
    """Filter out paths resolving to duplicates and print warning with duplicate count, if any."""
    seen = set()
    unique = []
    dupcount = 0
    for s in paths:
        s = os.path.normcase(os.path.abspath(s))
        if s in seen:
            dupcount += 1
        else:
            yield s
            seen.add(s)
    if dupcount:
        print(f'WARNING: duplicate input items ignored; count: {dupcount}')


def ensure_unique_names(paths):
    """Ensure all paths have unique base names and exit if not."""
    a = collections.Counter()
    for s in paths:
        a[os.path.basename(s)] += 1
    dups = [name for name, count in a.items() if count > 1]
    if dups:
        sys.exit(f'duplicate file names detected: {dups}')


def open_hash_file(dirpath, name):
    index = 0
    sfx = ''
    while True:
        try:
            path = os.path.join(dirpath, name + sfx + '.txt')
            return open(path, 'x', encoding='utf_8')
        except FileExistsError:
            index += 1
            sfx = '_' + str(index)


def main(args):
    inputfiles = list(prune_duplicates(expand_globs(args.input)))
    ensure_unique_names(inputfiles)

    hashfile = open_hash_file(args.destination, args.hashtype)

    for inpath in inputfiles:
        name = os.path.basename(inpath)
        outpath = os.path.join(args.destination, name)
        print(f'processing: {inpath}')
        h = hashlib.new(args.hashtype)
        with open(inpath, 'rb') as src, open(outpath, 'xb') as dst:
            for b in iter((lambda: src.read(args.bufsize)), b''):
                dst.write(b)
                h.update(b)
        print(h.hexdigest(), name, file=hashfile)


if __name__ == '__main__':
    main(parse_args())
