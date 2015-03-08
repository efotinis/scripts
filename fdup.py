"""Locate duplicate files using MD5 hashes."""

import os
import hashlib
import sys
import time
import collections
import string
import argparse

import CommonTools
import console_stuff
import winfixargv


HASH_BUFLEN = 2**20
STATUS_UPDATE_SEC = 1


class Status:
    def __init__(self, interval, counter):
        self.lastPrintTime = time.time()
        self.interval = interval
        self.counter = counter
        self.cursor = console_stuff.SamePosOutput(fallback=True)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.prnt()
        print
    def add(self, *data):
        self.counter.add(*data)
        t = time.time()
        if t - self.lastPrintTime >= self.interval:
            self.prnt()
            self.lastPrintTime = t
    def prnt(self):
        self.cursor.restore(True)
        print str(self.counter),
        sys.stdout.flush()


class ItemCounter:
    def __init__(self):
        self.value = 0
    def add(self, n):
        self.value += n
    def __str__(self):
        return str(self.value)


class SizeCounter:
    def __init__(self, total):
        self.current = 0
        self.total = total
    def add(self, n):
        self.current += n
    def __str__(self):
        percent = 100.0 * self.current / self.total if self.total else 100
##        return str(round(percent)) + '%'
        return str(int(round(percent))) + '%'


def fileList(dirname, recurse):
    """Generate the full paths of all files in a dir."""
    if recurse:
        for dpath, subs, files in os.walk(dirname):
            for s in files:
                yield os.path.join(dpath, s)
    else:
        for s in os.listdir(dirname):
            s = os.path.join(dirname, s)
            if os.path.isfile(s):
                yield s


def getSizeGroups(dirs, status, args):
    """Group all files in specified dirs by size."""
    ret = collections.defaultdict(list)
    for dir in dirs:
        for fpath in fileList(dir, args.recurse):
            fsize = os.path.getsize(fpath)
            if fsize != 0 or args.includezero:
                ret[fsize].append(fpath)
                status.add(1)
    return ret


def hashFile(fpath, status):
    """Calculate MD5 of file; return hash object."""
    f = open(fpath, 'rb')
    md5 = hashlib.md5()
    while True:
        s = f.read(HASH_BUFLEN)
        if not s:
            break
        md5.update(s)
        status.add(len(s))
    return md5
    

def sizeStr(n):
    """Convert byte count to str with unit and 2 decimals max."""
    if n < 1000:
        return str(n) + ' bytes'
    for c in 'KMGTPE':
        n /= 2.0**10
        if n < 999.5 or c == 'E':
            return '%.2f %ciB' % (n, c)


"""
options:
    dirs (list)
    masks (list, include/exclude)
    recurse (bool, for dirs)
    showempty (bool)
    ignoresigs (list)
"""


def hash_set_param(s):
    st = set(t.lower() for t in s.split(','))
    valid_digits = set(string.hexdigits)
    for x in st:
        if len(x) != 32:
            raise argparse.ArgumentTypeError('bad hash size: "%s"' % x)
        if not set(x) <= valid_digits:
            raise argparse.ArgumentTypeError('bad hash: "%s"' % x)
    return st


def parse_args():
    ap = argparse.ArgumentParser(
        description='locate duplicate files using MD5 hashes')
    add = ap.add_argument

    add('dirs', nargs='*', metavar='DIR', default=[u'.'],
        help='directory to scan ("." if none specified)')
    add('-r', dest='recurse', action='store_true',
        help='recurse into subdirectories')
    add('-e', dest='includezero', action='store_true',
        help='include empty files (ignored by default)')
    add('-i', dest='ignoresigs', type=hash_set_param, metavar='HASHES', default=[],
        help='ignore files with specified, comma-delimitied hashes')
    add('--delete', action='store_true',
        help='delete duplicates in each set except for one (randomly selected)')

    args = ap.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()

    print 'scanning:',
    with Status(STATUS_UPDATE_SEC, ItemCounter()) as status:
        sizeGroups = getSizeGroups(args.dirs, status, args)

    totalBytes = sum(size*len(files) for (size,files)
                     in sizeGroups.iteritems())
    bytesToHash = sum(size*len(files) for (size,files)
                      in sizeGroups.iteritems() if len(files) > 1)
    print 'total/hash size: %s, %s' % (sizeStr(totalBytes), sizeStr(bytesToHash))

    print 'hashing:',
    sigNames = collections.defaultdict(list)
    sigSizes = collections.defaultdict(int)
    ignored = 0
    with Status(STATUS_UPDATE_SEC, SizeCounter(bytesToHash)) as status:
        for size, files in sizeGroups.iteritems():
            if len(files) > 1:
                for s in files:
                    sig = hashFile(s, status).hexdigest()
                    if sig in args.ignoresigs:
                        ignored += 1
                    else:
                        sigNames[sig] += [s]
                        sigSizes[sig] = size

    print
    print 'duplicates:'
    for sig, files in sigNames.iteritems():
        if len(files) > 1:
            print '---- %s ----' % (sig,)
            for s in files:
                CommonTools.uprint('  ' + s)

    # calc and print dirs and their count of dup files
    dirs = collections.defaultdict(int)
    for sig, files in sigNames.iteritems():
        if len(files) > 1:
            for s in files:
                dirs[os.path.split(s)[0]] += 1

    print
    print 'dir counts:'
    for dir, times in sorted(dirs.items(), key=lambda t: t[1], reverse=True):
        print '  %6d: %s' % (times, dir)

    dupFiles, dupGroups = 0, 0
    dupBytes, uniqBytes = 0, 0
    for sig, files in sigNames.iteritems():
        if len(files) > 1:
            count, size = len(files), sigSizes[sig]
            dupFiles += count
            dupGroups += 1
            dupBytes += size * count
            uniqBytes += size
            
    #dups = [len(a) for a in sigNames.itervalues() if len(a) > 1]
    print
    print 'dup files/groups: %d, %d' % (dupFiles, dupGroups)
    print 'total/unique/extra size of dups: %s, %s, %s' % (
        sizeStr(dupBytes), sizeStr(uniqBytes), sizeStr(dupBytes - uniqBytes))
    print 'ignored files:', ignored

    if args.delete:
        print
        print 'deleting duplicates...'
        n = 0
        for sig, files in sigNames.iteritems():
            for s in files[1:]:  # keep the first one
                try:
                    os.unlink(s)
                    n += 1
                except OSError:
                    CommonTools.uprint('could not delete "%s"' % s)
        print 'files deleted:', n
