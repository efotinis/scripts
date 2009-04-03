##  id PACK extractor.
##
##  History:
##    2000-12:     Last C++ version (BC5.02)
##    2007-04-26:  Converted to Python 2.5.

import os
import sys
import struct


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BAD_PARAMS = 2


### convert an arbitrarily-sized little-endian byte string to an unsigned int
##strToUInt = lambda s: reduce(lambda a, b: a*256+ord(b), list(reversed(s)), 0)
##
##
### the above's reverse (32-bit)
##def uint32str(n):
##    n &= 0xffffffff
##    s = ''
##    for i in range(4):
##        s += chr(n & 0xff)
##        n >>= 8
##    return s


def errLn(s):
    sys.stderr.write('ERROR: ' + s + '\n')


##struct pakHdr {
##    char id[4];
##    ulong recTableOffset;
##    ulong recTableSize;
##};
pakHdr = struct.Struct('4sLL')
##struct fileInfo {
##    char name[56];
##    ulong offset;
##    ulong size;
##};
pakRec = struct.Struct('56sLL')


class PakFile:
    """An id-style PAK file. Currently only reading is allowed."""

    class Error(Exception):
        """Represent any error of this class."""
        def __init__(self, s):
            Exception.__init__(self, s)

    class Rec:
        """Information about each contained file in the PAK."""
        def __init__(self, name='', offs=0, size=0):
            self.name = name
            self.offs = offs
            self.size = size
        def __str__(self):
            return (self.name[:56].ljust(56, '\0') +
                    uint32str(self.offs) +
                    uint32str(self.size))

    def __init__(self, name, mode):
        """Open a file with an access mode."""
        self.f = file(name, mode)
        self.tableOffs = 0
        self.tableRecCnt = 0
        self.recs = []
        self._readHdr()
        self._readRecTable()

    def _readHdr(self):
        """Read header."""
        self.f.seek(0)
        s = self._readExactly(pakHdr.size, 'header')
        id, offs, size = pakHdr.unpack(s)
        if id <> 'PACK':
            raise Error('bad magic')
        self.tableOffs = offs
        self.tableRecCnt = size / pakRec.size
        
    def _readRecTable(self):
        """Read record table."""
        self.recs = []
        self.f.seek(self.tableOffs)
        for i in range(self.tableRecCnt):
            s = self._readExactly(pakRec.size, 'record')
            rec = self.Rec(*pakRec.unpack(s))
            if '\0' in rec.name:
                rec.name = rec.name[:rec.name.index('\0')]
            self.recs.append(rec)

    def _getItemIndex(self, name, softfail=False):
        """Return an item's index. If softfail is True, return -1 on error."""
        for i, rec in enumerate(self.recs):
            if name == rec.name and rec.offs <> 0:
                return i
        if softfail:
            return -1
        else:
            raise Error('item not found')

    def _readExactly(self, n, descr=None):
        """Read an exact number of bytes from the current pos."""
        s = self.f.read(n)
        if s < n:
            msg = 'EOF while reading'
            if descr:
                msg += ' ' + descr
            raise Error(msg)
        return s

    def getNames(self):
        """Return a list of the items' names."""
        return [rec.name for rec in self.recs]

    def getItemSize(self, name):
        """Return the size of an item."""
        return self.recs[self._getItemIndex(name)].size

    def getItem(self, name):
        """Return the data of an item."""
        rec = self.recs[self._getItemIndex(name)]
        self.f.seek(rec.offs)
        return self._readExactly(rec.size, 'item')

##    def removeItem(self, name):
##        del self.recs[self._getItemIndex(name)]
##
##    def setItem(self, name, s):
##        i = self._getItemIndex(name, softfail=True)
##        if 


def main(args):
    if '/?' in args:
        print 'Extract files from Quake2/Hexen2 packs.'
        print
        print 'Params: pakFile destDir'
        return EXIT_OK
    
    if len(args) == 2:
        pakFile, destDir = args
    else:
        errLn('Exactly 2 parameters are required.')
        return EXIT_BAD_PARAMS

    try:
        extract(pakFile, destDir)
        return EXIT_OK
    except PakFile.Error, x:
        errLn(str(x))
        return EXIT_ERROR


def extract(fname, destDir):
    pak = PakFile(fname, 'rb')
    for name in pak.getNames():
        print name
        data = pak.getItem(name)
        outPath = os.path.normpath(os.path.join(destDir, name))
        outDir = os.path.split(outPath)[0]
        if len(os.path.join(outDir, 'nul')) < len(os.path.join(destDir, 'nul')):
            raise PakFile.Error('Too many parent refs ("..") in rec "%s"' % name)
        if not os.path.isdir(outDir):
            os.makedirs(outDir)
        file(outPath, 'wb').write(data)


##sys.exit(main(sys.argv[1:]))


from collections import defaultdict
from pprint import pprint
import os

pak = PakFile(r'd:\games\Hexen II\data1\pak0.pak', 'rb')
d = defaultdict(int)
for s in pak.getNames():
##    if s.lower().endswith('.txt'):
##        print '-'*20, s, '-'*20
##        print pak.getItem(s)
    d[os.path.splitext(s)[1]] += 1
pprint(dict(d))
