#!python
"""Torrent file utilities.

When run as a script, it displays various types of information.
"""

from __future__ import print_function
import os
import re
import hashlib
import bencode
import sys
import pprint
import argparse
import glob


try:
    BSEP = bytes(os.path.sep, 'ascii')
except TypeError:
    BSEP = bytes(os.path.sep)


def calchash(obj):
    """String hash of a torrent bencode object.

    This is the SHA1 hexdigest of the 'info' dict.
    Source:
        Index >> Protocol Design Discussion >> How to get Hash out of .torrent file ?
        http://forum.utorrent.com/viewtopic.php?id=47411
    """
    data = bencode.dumps(obj[b'info'])
    return hashlib.sha1(data).hexdigest()


def filesinfo(obj):
    """Generate the full path and size of each file in a torrent bencode object."""
    if b'files' in obj[b'info']:
        for entry in obj[b'info'][b'files']:
            yield BSEP.join(entry[b'path']), entry[b'length']
    else:
        yield obj[b'info'][b'name'], obj[b'info'][b'length']


def parse_args():
    ap = argparse.ArgumentParser(description='print torrent contents')
    ap.add_argument('patterns', metavar='FILE', nargs='*',
                    help='torrent files (globs allowed)')
    group = ap.add_mutually_exclusive_group()
    group.add_argument('-x', dest='hashes', action='store_true',
                       help='print torrent hash and path instead')
    group.add_argument('-l', dest='listing', action='store_true',
                       help='print list of file sizes and paths instead')
    return ap.parse_args()


def gen_file_paths(patterns):
    """Generate file paths from script arguments.

    Additionally, print a warning when a pattern doesn't match anything.
    """
    for patt in patterns:
        paths = glob.glob(patt)
        if not paths:
            print('nothing matched "%s"' % patt, file=sys.stderr)
            continue
        for path in paths:
            yield path


if __name__ == '__main__':
    args = parse_args()

    for path in gen_file_paths(args.patterns):

        try:
            obj = bencode.load(open(path, 'rb'))
        except Exception as x:
            print('could not load "%s"; %s' % (path, x), file=sys.stderr)
            continue

        if args.hashes:
            try:
                hash = calchash(obj)
            except Exception as x:
                print('could not get hash of "%s"; %s' % (path, x), file=sys.stderr)
            else:
                print(hash, path)

        elif args.listing:            
            print(path)
            for item_path, size in filesinfo(obj):
                print('  %15d  %s' % (size, item_path))

        else:
            print('----', path)
            try:
                obj[b'info'][b'pieces'] = '<expunged>'
            except KeyError:
                pass
            pprint.pprint(obj)
            
