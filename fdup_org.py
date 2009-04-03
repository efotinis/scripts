# -*- coding: mbcs -*-
"""Locate duplicate files using MD5 hashes.

2007.10.14  EF  Created.
2008.03.09  EF  added cmdline options; renamed from 'finddups' to 'fdup'
"""

import os, hashlib, sys, time, collections
import DosCmdLine

IGNORE_SIGS = (
)
IGNORE_EMPTY = True
HASH_BUFLEN = 2**20
STATUS_UPDATE_SEC = 5


class Status:
    def __init__(self, interval, counter):
        self.lastPrintTime = time.time()
        self.interval = interval
        self.counter = counter
    def add(self, *data):
        self.counter.add(*data)
        t = time.time()
        if t - self.lastPrintTime >= self.interval:
            self.prnt()
            self.lastPrintTime = t
    def close(self):
        self.prnt()
        print
    def prnt(self):
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
        return str(round(100.0 * self.current / self.total)) + '%'


def getSizeGroups(root, status):
    ret = collections.defaultdict(list)
    for dpath, subs, files in os.walk(root):
        for s in files:
            fpath = os.path.join(dpath, s)
            fsize = os.path.getsize(fpath)
            if IGNORE_EMPTY and fsize == 0:
                continue
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

def buildSwitches():
    Swch = DosCmdLine.Switch
    Flag = DosCmdLine.Flag
    def mask_accum(s, a, include):
        return a + [(include, s.split(';'))]
    def inc_masks(s, a):
        return lambda s, a: mask_accum(s, a, True)
    def exc_masks(s, a):
        return lambda s, a: mask_accum(s, a, False)
    return (
        Flag('dirs', '',
             'One or more directories to scan. Default is the current one. '
             'If the last part of the path contains wildcards ',
             'it is automatically used as an include mask.'),
        Swch('I', 'masks',
             'Include masks (";"-delimited).',
             [], accumulator=inc_masks),
        Swch('E', 'masks',
             'Exclude masks (";"-delimited).',
             [], accumulator=exc_masks),
        Flag('R', 'recurse',
             'Recurse into subdirectories.'),
        Flag('Z', 'includezero',
             'Include 0 size files. By default, empty files are ignored.'),
        Swch('S', ignoresigs, 
             'Skip the specified sigs (";"-delimited). '
             'Use this to ignore certain files if needed.',
             [], accumulator=lambda s, a: a += s.split(';')),
        )
    """
    
    """


def main(root):
    print 'dir:', root

    print 'scanning files:',
    status = Status(STATUS_UPDATE_SEC, ItemCounter())
    sizeGroups = getSizeGroups(root, status)
    status.close()

    totalBytes = sum(size*len(files) for (size,files)
                     in sizeGroups.iteritems())
    bytesToHash = sum(size*len(files) for (size,files)
                      in sizeGroups.iteritems() if len(files) > 1)
    print 'total/hash: %s, %s' % (sizeStr(totalBytes), sizeStr(bytesToHash))

    print 'generating hashes:',
    sigMap = collections.defaultdict(list)
    status = Status(STATUS_UPDATE_SEC, SizeCounter(bytesToHash))
    for files in sizeGroups.itervalues():
        if len(files) > 1:
            for s in files:
                sig = hashFile(s, status).hexdigest()
                if sig not in IGNORE_SIGS:
                    sigMap[sig] += [s]
    status.close()
    
    dups = [len(a) for a in sigMap.itervalues() if len(a) > 1]
    print 'dups/groups:', sum(dups), len(dups)

    global uuuu
    uuuu = sigMap

    for sig, files in sigMap.iteritems():
        if len(files) > 1:
            print '-'*20, sig, '-'*20
            for s in files:
                try:
                    print s
                except UnicodeEncodeError:
                    print repr(s)
                    raise

    # calc and print dirs and their count of dup files
    dirs = collections.defaultdict(int)
    for sig, files in sigMap.iteritems():
        if len(files) > 1:
            for s in files:
                dirs[os.path.split(s)[0]] += 1
    print
    for dir,times in sorted(dirs.items(), key=lambda t: t[1]):
        print times, dir


uuuu = None
main(ur'D:\WORK')


##for dpath, subs, files in os.walk(ur'D:\WORK'):
##    for s in files:
##        fpath = os.path.join(dpath, s)
##        if os.path.getsize(fpath) == 296868:
##            print fpath


##foo = None
##for sig, files in uuuu.iteritems():
##    if len(files) > 1:
##        print '-'*20, sig, '-'*20
##        for s in files:
##            try:
##                print s
##            except UnicodeEncodeError, x:
##                foo = x
##                print repr(s)
##                raise
