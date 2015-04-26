"""Python implementation of the *nix fortune program.

See <http://en.wikipedia.org/wiki/Fortune_(Unix)>.
"""
from __future__ import print_function, division
import argparse
import codecs
import os
import random
import re
import struct
import sys
import time

import CommonTools


PY2 = sys.version_info.major == 2


def getfiles(all=False, offensive=False):
    """Get list of potential fortune files.

    Return non-offensive files by default. Use 'offensive' to get only offensive
    or 'all' for both (overrides 'offensive').
    Currently, only a single test directory is used.
    """
    nonoffensive = True
    if all:
        offensive = True
    elif offensive:
        nonoffensive = False
    FURTUNE_PATH = os.path.expandvars('%AppData%\\fortunes')
    # get all files without an extension
##    return [os.path.join(FURTUNE_PATH, s) for s in os.listdir(FURTUNE_PATH)
##            if not os.path.splitext(s)[1] and os.path.isfile(os.path.join(FURTUNE_PATH, s))]
    ret = []
    for dpath, subs, files in os.walk(FURTUNE_PATH):
        for s in files:
            if not os.path.splitext(s)[1]:
                ret += [os.path.join(dpath, s)]
    return ret


class Index(object):
    """Fortune index file."""
    VERSION = 1
    STR_RANDOM = 0x1
    STR_ORDERED = 0x2
    STR_ROTATED = 0x4
    HEADER = '>LLLLLc3s'
    HEADER_LEN = struct.calcsize(HEADER)

    def __init__(self, fpath):
        self.f = open(fpath, 'rb')
        hdr = self.f.read(self.HEADER_LEN)
        (self.version, self.count, self.maxlen, self.minlen,
         self.flags, self.delim, padding) = struct.unpack(self.HEADER, hdr)
        if not PY2:
            self.delim = str(self.delim, 'ascii')
        assert self.version == self.VERSION

    def __len__(self):
        """Number of strings."""
        return self.count

    def __getitem__(self, i):
        """Start/end of string; index can be negative."""
        if i < 0:
            i = self.count + i
        if i < 0 or i >= self.count:
            raise IndexError
        self.f.seek(self.HEADER_LEN + 4 * i)
        return struct.unpack('>LL', self.f.read(8))

    class _Iter(object):
        def __init__(self, ndx):
            self.ndx = ndx
            self.cur = 0
        def __iter__(self):
            return self
        def __next__(self):
            try:
                self.cur += 1
                return self.ndx[self.cur - 1]
            except IndexError:
                self.cur -= 1
                raise StopIteration
        next = __next__

    def __iter__(self):
        return self._Iter(self)


class File(object):
    """Fortune file supported by Index object."""
    ROT13_DECODER = codecs.getdecoder('rot13')
    
    def __init__(self, fpath, index):
        self.f = open(fpath, 'rt')
        self.index = index
        
    def __getitem__(self, i):
        """Get string; index can be negative.

        Automatically decodes ROT13-encoded data and removes delimiter line.
        """
        beg, end = self.index[i]
        self.f.seek(beg)
        s = self.f.read(end - beg)  # FIXME: non-ASCII text fails here with Py3
        if s[-2:] == self.index.delim + '\n':
            # this 'if' used to be an assert, but the delim+'\n'
            # of one file was missing at the last entry
            s = s[:-2]
        if self.index.flags & self.index.STR_ROTATED:
            s = ROT13_DECODER(s)[0]
        return s

    class _Iter(object):
        def __init__(self, dat):
            self.dat = dat
            self.cur = 0
        def __iter__(self):
            return self
        def __next__(self):
            try:
                self.cur += 1
                return self.dat[self.cur - 1]
            except IndexError:
                self.cur -= 1
                raise StopIteration
        next = __next__

    def __iter__(self):
        return self._Iter(self)


def makesizefilter(onlylong, onlyshort, shortlen):
    """Create a size-filtering function."""
    if onlyshort:
        return lambda n: n <= shortlen
    elif onlylong:
        return lambda n: n > shortlen
    else:
        return lambda n: True


def countitems(indexfile, sizefilter):
    """Count the items that satisfy the specified size constraints."""
    count = 0
    try:
        for beg, end in Index(indexfile):
            if sizefilter(end - beg - 2):
                count += 1
        return count
    except IOError:
        # probably index file not found
        return 0


def findnth(ndx, n, sizefilter):
    for i, (beg, end) in enumerate(ndx):
        if not sizefilter(end - beg - 2):
            continue
        if n == 0:
            return i
        n -= 1
    raise IndexError


def indexname(s):
    """Convert fortune file name to index name.

    Replaces extension with 'dat'.
    """
    s, ext = os.path.splitext(s)
    return s + '.dat'


def parse_args():
    ap = argparse.ArgumentParser(
        description='Unix fortune in Python')

    grp = ap.add_argument_group('filters')
    add = grp.add_argument
    add('-a', dest='all', action='store_true',
        help='choose from all databases, regardless of whether they are '
        'considered "offensive"')
    add('-o', dest='offensive', action='store_true',
        help='choose only from "offensive" databases')
    add('-e', dest='equalfileprob', action='store_true',
        help='make the probability of choosing a fortune file equal to '
        'that of all other files')
    grp2 = grp.add_mutually_exclusive_group()
    add2 = grp2.add_argument
    add2('-l', dest='onlylong', action='store_true',
        help='use only long quotations; see -n')
    add2('-s', dest='onlyshort', action='store_true',
        help='use only short quotations; see -n')
    add('-n', dest='shortlen', type=int, default=160, metavar='LEN', 
        help='specify the size boundary between short and long '
        'quotations; default: %(default)s')

    grp = ap.add_argument_group('listing')
    add = grp.add_argument
    add('-f', dest='filenamesonly', action='store_true',
        help='print out a list of all fortune files that would have been '
        'searched, but do not print a fortune')
    add('-m', dest='matchpattern', metavar='PATT', 
        help='print all fortunes matching the regexp specified; see -c')
    add('-i', dest='ignorecase', action='store_true',
        help='make the regexp of -m case-insensitive')

    grp = ap.add_argument_group('misc')
    add = grp.add_argument
    add('-w', dest='wait', action='store_true',
        help='wait for a period of time (proportionate to the quotation '
        'size) before exiting')

    grp = ap.add_argument_group('extensions')
    add = grp.add_argument
    add('-j', dest='showsource', action='store_true',
        help='prepend source file/index to quotations')
    add('-c', dest='countmatches', action='store_true',
        help='when used with -m, print count of matches instead')

    args = ap.parse_args()

    # TODO: support input files

    rxflags = re.DOTALL
    if args.ignorecase:
        rxflags |= re.IGNORECASE
    if args.matchpattern:
        try:
            args.matchpattern = re.compile(args.matchpattern, rxflags)
        except re.error as x:
            ap.error('invalid regexp; ' + str(err))

    return args


if __name__ == '__main__':
    args = parse_args()

    # get paths of files
    files = getfiles(args.all, args.offensive)

    # if requested, show filenames and exit
    if args.filenamesonly:
        for s in files:
            print(s)
        sys.exit()

    sizefilter = makesizefilter(args.onlylong, args.onlyshort, args.shortlen)

    # if pattern matching is requested, show items and exit
    if args.matchpattern:
        count = 0
        for datafile in files:
            try:
                ndx = Index(indexname(datafile))
                for i, s in enumerate(File(datafile, ndx)):
                    if sizefilter(len(s)) and args.matchpattern.search(s):
                        if args.countmatches:
                            count += 1
                        else:
                            if args.showsource:
                                print('[%s:%d]' % (datafile, i))
                            sys.stdout.write(s + ndx.delim + '\n')
            except IOError:
                # probably index file not found
                pass
        if args.countmatches:
            print(count, 'matches')
        sys.exit()
                    
    # count items according to size constaints
    counts = [countitems(indexname(s), sizefilter) for s in files]

    if not files:
        sys.exit('no fortune files')

    # remove files and counts when count is 0
    # FIXME: fails when all items are removed
    files, counts = zip(*[
        (s, n) for (s, n) in zip(files, counts)
        if n])

    if not files:
        sys.exit('nothing matches criteria')

    if args.equalfileprob:
        filename, count = random.choice(zip(files, counts))
        i = random.randint(0, count-1)
    else:
        i = random.randint(0, sum(counts)-1)
        files = list(files)
        counts = list(counts)
        while i >= counts[0]:
            i -= counts[0]
            del files[0]
            del counts[0]
        filename = files[0]

    ndx = Index(indexname(filename))
    i = findnth(ndx, i, sizefilter)
    message = File(filename, ndx)[i]
    if args.showsource:
        print('[%s:%d]' % (filename, i))
    sys.stdout.write(message)
    if args.wait:
        time.sleep(2 + (len(message) / 20))
