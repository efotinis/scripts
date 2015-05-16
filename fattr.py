"""File attribute statistics."""

import os
import sys
import argparse
import collections

import CommonTools
import six
import win32file


INVALID_FILE_ATTRIBUTES = 0xffffffff


FLAG_NAMES = collections.defaultdict(
    lambda: '?',
    {
        0x1: 'readonly',
        0x2: 'hidden',
        0x4: 'system',
        0x10: 'directory',
        0x20: 'archive',
        0x40: 'device',
        0x80: 'normal',
        0x100: 'temporary',
        0x200: 'sparse_file',
        0x400: 'reparse_point',
        0x800: 'compressed',
        0x1000: 'offline',
        0x2000: 'not_content_indexed',
        0x4000: 'encrypted',
        0x8000: 'integrity_stream',
        0x20000: 'no_scrub_data',
        0x10000: 'virtual',
    }
)


def parse_args():
    ap = argparse.ArgumentParser(description='file attribute statistics')

    def flags_int(s):
        return int(s, 0)

    ap.add_argument('paths', metavar='DIR', nargs='*', default=['.'], help='source directory (default is ".")')
    ap.add_argument('-l', dest='listmask', type=flags_int, help='list files with specified flags; suppresses flag statistics output')

    group = ap.add_mutually_exclusive_group()
    group.add_argument('-d', dest='include_dirs', action='store_true', help='process directories as well')
    group.add_argument('-D', dest='dirs_only', action='store_true', help='process directories only')

    args = ap.parse_args()
    args.paths = map(six.text_type, args.paths)
    return args


if __name__ == '__main__':
    args = parse_args()
    counter = collections.Counter()
    item_count = 0
    FLAGS = [1<<i for i in range(32)]

    if args.include_dirs:
        do_files = True
        do_dirs = True
    elif args.dirs_only:
        do_files = False
        do_dirs = True
    else:
        do_files = True
        do_dirs = False

    for dir_path in args.paths:
        if not os.path.isdir(dir_path):
            CommonTools.conerr('not a directory: "%s"' % dir_path)
            continue
        for p,d,f in os.walk(dir_path):
            items = []
            if do_dirs:
                items += d
            if do_files:
                items += f
            for s in items:
                path = os.path.join(p, s)
                attr = win32file.GetFileAttributesW(path) & 0xffffffff
                if attr == INVALID_FILE_ATTRIBUTES:
                    CommonTools.conerr('could not get attributes of "%s"' % path)
                    continue
                for n in FLAGS:
                    if attr & n:
                        counter[n] += 1
                if args.listmask is not None and attr & args.listmask:
                    CommonTools.conout(path)
                item_count += 1

    if args.listmask is None:
        max_flag_name_len = max(len(s) for s in FLAG_NAMES.values())
        for n in FLAGS:
            if counter[n]:
                print '%*s (0x%08x) %6d' % (max_flag_name_len, FLAG_NAMES[n], n, counter[n])
        print 'total items: %d' % item_count
