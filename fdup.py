# -*- coding: mbcs -*-
"""Locate duplicate files using MD5 hashes.

2007.10.14  EF  created
2008.03.09  EF  added cmdline options; renamed from 'finddups' to 'fdup'
2008.03.20  EF  used console_stuff.SamePosOutput;
                added display of total/uniq/extra size of dups;
                reversed order of dir freqs (descending)
"""

from __future__ import with_statement
import os, hashlib, sys, time, collections, string
import DosCmdLine, CommonTools, console_stuff

HASH_BUFLEN = 2**20
STATUS_UPDATE_SEC = 1


class Status:
    def __init__(self, interval, counter):
        self.lastPrintTime = time.time()
        self.interval = interval
        self.counter = counter
        self.cursor = console_stuff.SamePosOutputTry()
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


def getSizeGroups(dirs, status, opt):
    """Group all files in specified dirs by size."""
    ret = collections.defaultdict(list)
    for dir in dirs:
        for fpath in fileList(dir, opt.recurse):
            fsize = os.path.getsize(fpath)
            if fsize != 0 or opt.includezero:
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


def validateSigList(a):
    """Check sig-ignore list and convert to a set for fast testing."""
    ret = set()
    validChars = set(string.hexdigits)
    for s in a:
        if len(s) > 32:
            raise DosCmdLine.Error('sig too long: "%s"' % s)
        else:
            s = s.rjust(32, '0')
        if set(s) > validChars:
            raise DosCmdLine.Error('bad sig chars: "%s"' % s)
        ret.add(s.lower())
    return ret
        

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
##    def mask_accum(s, a, include):
##        return a + [(include, s.split(';'))]
##    def inc_masks(s, a):
##        return lambda s, a: mask_accum(s, a, True)
##    def exc_masks(s, a):
##        return lambda s, a: mask_accum(s, a, False)
    return (
        Flag('dirs', '',
             'One or more directories to scan. Default is the current one. '
             #'If the last part of the path contains wildcards '
             #'it is automatically used as an include mask.'
             ),
##        Swch('I', 'masks',
##             'Include masks (";"-delimited).',
##             [], accumulator=inc_masks),
##        Swch('E', 'masks',
##             'Exclude masks (";"-delimited).',
##             [], accumulator=exc_masks),
        Flag('R', 'recurse',
             'Recurse into subdirectories.'),
        Flag('Z', 'includezero',
             'Include 0-size files. By default, empty files are ignored.'),
        Swch('S', 'ignoresigs', 
             'Skip the specified sigs (";"-delimited). '
             'Use this to ignore certain files if needed.',
             [], accumulator=lambda s, a: a + s.split(';')),
        )


def showHelp(switches):
    """Print help."""
    print """Locate duplicate files using MD5 hashes.

%s [/R] [/Z] [/S:skip] [dirs...]

%s""" % (
    CommonTools.scriptname().upper(),
    '\n'.join(DosCmdLine.helptable(switches)))


def main(args):
    switches = buildSwitches()
    if '/?' in args:
        showHelp(switches)
        return 0
    try:
        opt, params = DosCmdLine.parse(args, switches)
        if not params:
            params = ['.']
        params = map(unicode, params)
        opt.ignoresigs = validateSigList(opt.ignoresigs)
    except DosCmdLine.Error, x:
        CommonTools.errln(str(x))
        return 2

    print 'scanning:',
    with Status(STATUS_UPDATE_SEC, ItemCounter()) as status:
        sizeGroups = getSizeGroups(params, status, opt)

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
                    if sig in opt.ignoresigs:
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
    print 'total/uniq/extra size of dups: %s, %s, %s' % (
        sizeStr(dupBytes), sizeStr(uniqBytes), sizeStr(dupBytes - uniqBytes))
    print 'ignored files:', ignored


sys.exit(main(sys.argv[1:]))        
