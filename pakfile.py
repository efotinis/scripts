"""id's PAK file utilities."""

import os
import sys
import struct

import fileutil
import CommonTools
import six

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


# struct pakHdr {
#   char id[4];
#   ulong recTableOffset;
#   ulong recTableSize;
# };
# struct fileInfo {
#   char name[56];
#   ulong offset;
#   ulong size;
# };
RECORD_NAME_SIZE = 56
HEADER = struct.Struct('4sLL')
RECORD = struct.Struct(str(RECORD_NAME_SIZE) + 'sLL')


class Error(Exception):
    pass


class Record:

    def __init__(self, f):
        self.f = f
        s = fileutil.readexactly(f, RECORD.size)
        self.name, self.offset, self.size = RECORD.unpack(s)
        eos = self.name.find('\0')
        if eos != -1:
            self.name = self.name[:eos]

##    def pack(self):
##        # name will be 0-padded if shorter, but check that it isn't truncated
##        if len(self.name) > RECORD_NAME_SIZE:
##            raise ValueError('record name too long')
##        return RECORD.pack(self.name, self.offset, self.size)
##
    def read(self):
        self.f.seek(self.offset)
        return fileutil.readexactly(self.f, self.size)


class PakFile(object):
    """A PAK (id/Quake) file."""

    def __init__(self, file, mode='r'):
        self.ownhandle = isinstance(name, six.string_types)
        if self.ownhandle:
            if 'b' not in self.mode:
                self.mode += 'b'
            self.file = open(file, mode)
        else:
            self.mode = file.mode
            if 'b' not in self.mode:
                raise Error('file not opened as binary')
            self.file = file
        self.name
        self.f = open(name, mode)
        self.records = []
        self.readtable(*self.readheader())

    def close(self):
        self.f.close()

    def readheader(self):
        """Read the PAK header and return table offset and record count."""
        self.f.seek(0)
        s = fileutil.readexactly(self.f, HEADER.size)
        magic, offset, size = HEADER.unpack(s)
        if magic != 'PACK':
            raise Error('bad magic')
        if size % RECORD.size != 0:
            raise Error('table size not a multiple of record size')
        return offset, size / RECORD.size
        
    def readtable(self, offset, count):
        """Read the records table."""
        self.records = []
        self.f.seek(offset)
        for i in range(count):
            self.records.append(Record(self.f))

    def getrecords(self):
        return self.records[:]

    def read(self, name):
        # always append, even if a large enough record exists
        pass

    def write(self, name, data):
        # always append, even if a large enough record exists
        pass


##    def __getitem__(self, name):
##        for rec in self.records:
##            if rec.name == name and rec.offs != 0:
##                return rec
##        raise KeyError(name)
##
##    def getNames(self):
##        """Return a list of the items' names."""
##        return [rec.name for rec in self.records]
##
##    def getItemSize(self, name):
##        """Return the size of an item."""
##        return self.getrecord(name).size
##
##    def getItemData(self, name):
##        """Return the data of an item."""
##        rec = self.getrecord(name)
##        self.f.seek(rec.offs)
##        return fileutil.readexactly(self.f, rec.size)

##    def removeItem(self, name):
##        del self.records[self._getItemIndex(name)]
##
##    def setItem(self, name, s):
##        i = self._getItemIndex(name, softfail=True)
##        if 


##def main(args):
##    if '/?' in args:
##        print 'Extract files from Quake2/Hexen2 packs.'
##        print
##        print 'Params: pakFile destDir'
##        return EXIT_OK
##    
##    if len(args) == 2:
##        pakFile, destDir = args
##    else:
##        CommonTools.errln('Exactly 2 parameters are required.')
##        return EXIT_BAD_PARAMS
##
##    try:
##        extract(pakFile, destDir)
##        return EXIT_OK
##    except Error as x:
##        CommonTools.errln(str(x))
##        return EXIT_ERROR
##
##
##def extract(fname, destDir):
##    pak = PakFile(fname, 'rb')
##    for name in pak.getNames():
##        print name
##        data = pak.getItemData(name)
##        outPath = os.path.normpath(os.path.join(destDir, name))
##        outDir = os.path.split(outPath)[0]
##        if len(os.path.join(outDir, 'nul')) < len(os.path.join(destDir, 'nul')):
##            raise Error('Too many parent refs ("..") in rec "%s"' % name)
##        if not os.path.isdir(outDir):
##            os.makedirs(outDir)
##        open(outPath, 'wb').write(data)
##
##
####sys.exit(main(sys.argv[1:]))
##
##
##from collections import defaultdict
##from pprint import pprint
##import os
##
##pak = PakFile(r'd:\games\Hexen II\data1\pak0.pak', 'rb')
##d = defaultdict(int)
##for s in pak.getNames():
####    if s.lower().endswith('.txt'):
####        print '-'*20, s, '-'*20
####        print pak.getItemData(s)
##    d[os.path.splitext(s)[1]] += 1
##pprint(dict(d))

pak = PakFile(r"C:\Users\Elias\Desktop\pak0.pak", 'rb')

from collections import defaultdict as ddict
d = ddict(int)
for rec in pak.getrecords():
    d[os.path.splitext(rec.name)[1]] += 1
print d



'''                                       r   w   a   r+  w+  a+
                                          ----------------------
    file must exist before open           x   -   -   x   -   -
    old file contents discarded on open   -   x   -   -   x   -
    stream can be read                    x   -   -   x   x   x
    stream can be written                 -   x   x   x   x   x
    stream can be written only at end     -   -   x   -   -   x
'''


'''
usage:

pak = PakFile('test.pak')
for rec in pak.


'''


##------------------
## 17:38 07/12/2011
##------------------

def read_file_struct(fp, s, offset=None):
    if offset is not None:
        fp.seek(offset)
    return struct.unpack(fmt, CommonTools.readexactly(s.size))


PAK_MODE_TO_ACCESS = {
    'r': 'r',
    'w': 'wa',
    'a': 'a',
    'r+': 'rwa',
    'w+': 'rwa',
    'a+': 'ra',
    }
PAK_MODE_TO_FILE_MODE = { ...
    'r': 'rb',
    'w': 'r+b',
    'a': 'r+b',
    'r+': 'r+b',
    'w+': 'r+b',
    'a+': 'ra',
    }


class PakFile(object):

    def __init__(self, path, mode='r'):
        if not re.match(r'^[rwa]\+?$', mode):
            raise ValueError('invalid mode')

        self.mode = PAK_MODE_TO_ACCESS[mode]        
        self.fp = open(path, PAK_MODE_TO_FILE_MODE[mode])
        
        magic, dir_offs, dir_size = read_file_struct(self.fp, HEADER)
        if magic != 'PACK':
            raise ValueError('not a PAK file')
        self.fp.seek(dir_offs)
        reccount = dir_size // struct.calcsize(RECORD)
        self.entries = [Entry.from_file(self.fp) for i in range(reccount)]

    def __iter__(self):
        """Iterator for entries (Entry objects)."""
        return iter(self.entries)

    def names(self):
        """Iterator of item names."""
        for item in self.entries:
            yield item.name

    def items(self):
        """Iterator of items."""
        for item in self.entries:
            yield item

    def find(self, name):
        """Get the *first* Entry object with specified name."""
        for item in self.entries:
            if item.name == name:
                return item
        raise ValueError('item not found: "%s"' % name)

    def get(self, x):
        if not isinstance(x, Entry):
            x = self.find(x)
        

class Entry:

    @classmethod
    def from_file(cls, fp):
        name, offset, size = read_file_struct(fp, RECORD)
        name = name.partition('\0')[0]
        return cls(name, offset, size)

    def __init__(self, name, offset, size):
        self.name = name
        self.offset = offset
        self.size = size


"""
open()
---------------------------------------------------------------------------
            missing     exists      read    modify  add

    r       fail        open        yes     no      no
    w       create      trunc       no      yes     yes
    a       create      open        no      no      yes
    r+      fail        open        yes     yes     yes
    w+      create      trunc       yes     yes     yes
    a+      create      open        yes     no      yes


PakFile()
---------------------------------------------------------------------------
            missing     exists      read    modify  add     file mode
            
    r       fail        open        yes     no      no      r
    w       create      trunc       no      yes     yes     w+
    a       create      open        no      no      yes     r+ -> w+
    r+      fail        open        yes     yes     yes     r+
    w+      create      trunc       yes     yes     yes     w+
    a+      create      open        yes     no      yes     r+ -> w+
"""





'''                                       r   w   a   r+  w+  a+
                                          ----------------------
    file must exist before open           x   -   -   x   -   -
    old file contents discarded on open   -   x   -   -   x   -
    stream can be read                    x   -   -   x   x   x
    stream can be written                 -   x   x   x   x   x
    stream can be written only at end     -   -   x   -   -   x


r       read            open existing
w       write           create new
a       append          open/create
r+      read/write      open existing
w+      read/write      create new
a+      read/append     open/create
'''
