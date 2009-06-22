"""Python implementation of the *nix fortune program.

See <http://en.wikipedia.org/wiki/Fortune_(Unix)>.
"""
import os
import sys
import random
import getopt
import struct
import re
import codecs
import time

import CommonTools


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
        def next(self):
            try:
                self.cur += 1
                return self.ndx[self.cur - 1]
            except IndexError:
                self.cur -= 1
                raise StopIteration

    def __iter__(self):
        return self._Iter(self)


class File(object):
    """Fortune file supported by Index object."""
    ROT13_DECODER = codecs.getdecoder('rot13')
    
    def __init__(self, fpath, index):
        self.f = open(fpath, 'rb')
        self.index = index
        
    def __getitem__(self, i):
        """Get string; index can be negative.

        Automatically decodes ROT13-encoded data and removes delimiter line.
        """
        beg, end = self.index[i]
        self.f.seek(beg)
        s = self.f.read(end - beg)
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
        def next(self):
            try:
                self.cur += 1
                return self.dat[self.cur - 1]
            except IndexError:
                self.cur -= 1
                raise StopIteration

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


def parsecmdline():
    """Parse cmdline and return options and arguments."""
    opt, args = getopt.gnu_getopt(sys.argv[1:], '?aoefm:ilsn:wjc')
    if args:
        raise getopt.GetoptError('arguments not supported yet')

    d = {'help':False, 'all':False, 'offensive':False, 'equalfileprob':False,
         'filenamesonly':False, 'matchpattern':None, 'onlylong':False,
         'onlyshort':False, 'shortlen':160, 'wait':False, 'showsource':False,
         'countmatches':False}
    casesens = True
    patt = ''
    for sw, val in opt:
        if sw == '-?':   d['help'] = True
        elif sw == '-a': d['all'] = True
        elif sw == '-o': d['offensive'] = True
        elif sw == '-e': d['equalfileprob'] = True
        elif sw == '-f': d['filenamesonly'] = True
        elif sw == '-m': patt = val
        elif sw == '-i': casesens = False
        elif sw == '-l': d['onlylong'] = True
        elif sw == '-s': d['onlyshort'] = True
        elif sw == '-n': d['shortlen'] = int(val)
        elif sw == '-w': d['wait'] = True
        elif sw == '-j': d['showsource'] = True
        elif sw == '-c': d['countmatches'] = True
    if d['onlylong'] and d['onlyshort']:
        raise getopt.GetoptError('-l and -s are mutually exclusive')
    if patt:
        flags = re.DOTALL | (0 if casesens else re.IGNORECASE)
        try:
            d['matchpattern'] = re.compile(patt, flags)
        except re.error as err:
            raise getopt.GetoptError('invalid regexp: ' + str(err))
    opt = d
    return opt, args


def showhelp():
    scriptname = CommonTools.scriptname().upper()
    print '''
Python implementation of *nix fortune.

%(scriptname)s [options]

         [Filters]
  -a       Choose from all databases, regardless of whether they are considered
           "offensive".
  -o       Choose only from "offensive" databases.
  -e       Make the probability of choosing a fortune file equal to that of all
           other files
  -l       Use only long quotations (see -n).
  -s       Use only short quotations (see -n).
  -n LEN   Specify the size boundary between short and long quotations.
           Default is 160.

         [Listing]
  -f       Print out a list of all fortune files that would have been searched,
           but do not print a fortune.
  -m PATT  Print all fortunes matching the regexp specified. See also -c.
  -i       Make the regexp of -m case-insensitive.
  
         [Misc]
  -w       Wait for a period of time (proportionate to the quotation size)
           before exiting.

         [Extensions]
  -j       Prepend source file/index to quotations.
  -c       When used with -m, print count of matches instead.
           
'''[1:-1] % locals()


def main():
    try:
        opt, args = parsecmdline()
    except getopt.GetoptError as err:
        raise SystemExit(err)

    if opt['help']:
        showhelp()
        return

    # get paths of files
    files = getfiles(opt['all'], opt['offensive'])

    # if requested, show filenames and exit
    if opt['filenamesonly']:
        for s in files:
            print s
        return

    sizefilter = makesizefilter(opt['onlylong'], opt['onlyshort'], opt['shortlen'])

    # if pattern matching is requested, show items and exit
    if opt['matchpattern']:
        count = 0
        for datafile in files:
            try:
                ndx = Index(indexname(datafile))
                for i, s in enumerate(File(datafile, ndx)):
                    if sizefilter(len(s)) and opt['matchpattern'].search(s):
                        if opt['countmatches']:
                            count += 1
                        else:
                            if opt['showsource']:
                                print '[%s:%d]' % (datafile, i)
                            sys.stdout.write(s + ndx.delim + '\n')
            except IOError:
                # probably index file not found
                pass
        if opt['countmatches']:
            print count, 'matches'
        return
                    
    # count items according to size constaints
    counts = [countitems(indexname(s), sizefilter) for s in files]

    if not files:
        raise SystemExit('no fortune files')

    # remove files and counts when count is 0
    # FIXME: fails when all items are removed
    files, counts = zip(*[
        (s, n) for (s, n) in zip(files, counts)
        if n])

    if not files:
        raise SystemExit('nothing matches criteria')

    if opt['equalfileprob']:
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
    if opt['showsource']:
        print '[%s:%d]' % (filename, i)
    sys.stdout.write(message)
    if opt['wait']:
        time.sleep(2 + (len(message) / 20.0))


main()