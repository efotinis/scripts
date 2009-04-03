##  Info from fatgen103.doc
##  <http://download.microsoft.com/download/1/6/1/161ba512-40e2-4cc9-843a-923143f3456c/fatgen103.doc>:
##    Hardware White Paper 	
##    Designing Hardware for Microsoft Operating Systems
##    Microsoft Extensible Firmware Initiative FAT32 File System Specification
##    FAT: General Overview of On-Disk Format
##    Version 1.03, December 6, 2000
##    Microsoft Corporation

import os
import sys
import hashlib

# TODO: use 'struct' module

# TODO: write a func to tranlate a C struct to a struct.Struct
#       e.g.
#           s = """struct Foo {
#               int x;  // name_to_use_instead
#               char s[10];
#           }"""
#           s = makeStruct(s)  # ==> struct.Struct('i10s')


def showBootSector(drive):
    f = file('\\\\?\\' + drive, 'rb')
    s = f.read(512)
    f.close()

    w = 16
    for i in range(0, 512, w):
        print hexDump(s[i:i+w], w)


def hexDump(s, w):
    s1 = ''
    s2 = ''
    for i in range(w):
        if i < len(s):
            c = ord(s[i])
            s1 += '%02X ' % c
            s2 += (s[i] if 32 <= c <= 127 else '.')
        else:
            s1 += '   '
            s2 += ' '
    return s1 + ' ' + s2


common = [
    ('BS_jmpBoot',     'b', 3),
    ('BS_OEMName',     's', 8),
    ('BPB_BytsPerSec', 'u', 2),
    ('BPB_SecPerClus', 'u', 1),
    ('BPB_ResvdSecCnt','u', 2),
    ('BPB_NumFATs',    'u', 1),
    ('BPB_RootEntCnt', 'u', 2),
    ('BPB_TotSec16',   'u', 2),
    ('BPB_Media',      'u', 1),
    ('BPB_FATSz16',    'u', 2),
    ('BPB_SecPerTrk',  'u', 2),
    ('BPB_NumHeads',   'u', 2),
    ('BPB_HiddSec',    'u', 4),
    ('BPB_TotSec32',   'u', 4)
]


fat1216 = [
    ('BS_DrvNum',     'u', 1),
    ('BS_Reserved1',  'u', 1),
    ('BS_BootSig',    'u', 1),
    ('BS_VolID',      'u', 4),
    ('BS_VolLab',     's', 11),
    ('BS_FilSysType', 's', 8),
]


fat32 = [
    ('BPB_FATSz32',   'u', 4),
    ('BPB_ExtFlags',  'u', 2),
    ('BPB_FSVer',     'u', 2),
    ('BPB_RootClus',  'u', 4),
    ('BPB_FSInfo',    'u', 2),
    ('BPB_BkBootSec', 'u', 2),
    ('BPB_Reserved',  'b', 12),
    ('BS_DrvNum',     'u', 1),
    ('BS_Reserved1',  'u', 1),
    ('BS_BootSig',    'u', 1),
    ('BS_VolID',      'u', 4),
    ('BS_VolLab',     's', 11),
    ('BS_FilSysType', 's', 8)
]


def showBootSector2(drive):
    f = file('\\\\?\\' + drive, 'rb')
    s = f.read(512)
    f.close()

    if len(s) < 512:
        print 'Could not read the first 512 bytes'
        return

    fields = common + fat1216
    dumpFields(fields, s)
    print

    print '0x55AA sig at offset 510:',
    if s[-2:] == '\x55\xAA':
        print 'Found'
    else:
        print 'Not found'
    print

    bs = getStruct(fields, s)
    RootDirSectors = ((bs.BPB_RootEntCnt * 32) + (bs.BPB_BytsPerSec - 1)) / bs.BPB_BytsPerSec;
    FATSz = (bs.BPB_FATSz16 if bs.BPB_FATSz16 != 0 else bs.BPB_FATSz32)
    FirstDataSector = bs.BPB_ResvdSecCnt + (bs.BPB_NumFATs * FATSz) + RootDirSectors;
    TotSec = (bs.BPB_TotSec16 if bs.BPB_TotSec16 != 0 else bs.BPB_TotSec32)
    DataSec = TotSec - (bs.BPB_ResvdSecCnt + (bs.BPB_NumFATs * FATSz) + RootDirSectors)

    CountofClusters = DataSec / bs.BPB_SecPerClus

    if CountofClusters < 4085:
        FATEntryBits = 12
    elif CountofClusters < 65525:
        FATEntryBits = 16
    else:
        FATEntryBits = 32
    print 'Volume type is FAT' + str(FATEntryBits)
    print 'Count of data clusters (excl. reserved 2):', CountofClusters
    print

    # FATSz is the size in sectors, but not all bytes are valid.
    # Only the first 'CountofClusters + 2' entries are valid; the rest are 0.

    fats = []
    start = 1
    for i in range(bs.BPB_NumFATs):
        fat = getSectors(start, FATSz, bs)
        fats += [fat]
        start += FATSz
    for i in range(len(fats)-1):
        if fats[i] != fats[i+1]:
            print 'FATs %d and %d are different' % (i, i+1)
            return

    dumpFAT12(fats[0], CountofClusters + 2)

    print 'Done'            


def dumpFAT12(s, entries):
    assert len(s) % 3 == 0
    clusters = []
    for i in range(0, len(s), 3):
        mixed = valUInt(s[i:i+3])
        n1 = mixed & 0xFFF
        n2 = mixed >> 12
        clusters += [fat12ClusterType(n1), fat12ClusterType(n2)]
        if len(clusters) >= entries:
            clusters[entries:] = []  # remove excess
            break;
    clusters[0] = clusters[1] = 'R'
    for i in range(len(clusters)):
        sys.stdout.write(clusters[i])
        if (i + 1) % 64 == 0:
            print
    print


def fat12ClusterType(n):
    if n == 0: return '.'      # free
    if n == 0xFF7: return 'X'  # bad
    if n >= 0xFF8: return 'o'  # allocated (last in chain)
    return 'O'                 # allocated


def getSectors(drive, start, count, bs):
    f = file('\\\\?\\' + drive, 'rb', 0)
    f.seek(start * bs.BPB_BytsPerSec)
    bytes = count * bs.BPB_BytsPerSec
    ret = f.read(bytes)
    if len(ret) != bytes:
        raise '(could not read all the requested sectors)'
    return ret


def dumpFields(fields, mem):
    maxNameLen = max([len(f[0]) for f in fields])
    offs = 0
    for f in fields:
        print f[0].rjust(maxNameLen) + ': ' + fieldFmt(f, mem, offs)
        offs += f[2]


class Struct:
    pass


def getStruct(fields, mem):
    ret = Struct()
    offs = 0
    for f in fields:
        setattr(ret, f[0], fieldVal(f, mem, offs))
        offs += f[2]
    return ret


def fieldFmt(f, mem, offs):
    data = mem[offs:offs+f[2]]
    if len(data) != f[2]: return '(unsufficient data)'
    if f[1] == 'u': return fmtUInt(data)
    if f[1] == 'b': return fmtBin(data)
    if f[1] == 's': return fmtStr(data)
    return '(unknown type)'


def fieldVal(f, mem, offs):
    data = mem[offs:offs+f[2]]
    if len(data) != f[2]: raise '(unsufficient data)'
    if f[1] == 'u': return valUInt(data)
    if f[1] == 'b': return valBin(data)
    if f[1] == 's': return valStr(data)
    raise '(unknown type)'


def fmtUInt(s):
    x = ''
    n = 0
    f = 1
    for c in s:
        x = ('%02X' % ord(c)) + x
        n += ord(c) * f
        f *= 256
    return '0x%s (%d)' % (x, n)

    
def fmtBin(s):
    ret = ''
    for c in s:
        ret += '%02X' % ord(c)
    return ret

    
def fmtStr(s):
    return "'" + s + "'"
    

def valUInt(s):
    n = 0
    f = 1
    for c in s:
        n += ord(c) * f
        f *= 256
    return n

    
def valBin(s):
    return s

    
def valStr(s):
    return s
    

#showBootSector()
#showBootSector2()


def boolMsg(x, msgs):
    return msgs[bool(x)]
def foundMsg(x):
    return boolMsg(x, ['Not found', 'Found'])


class DriveError(Exception):
    def __init__(self, s):
        self.msg = s
    def __str__(self):
        return self.msg


def clusterGraphType12(n):
    if n == 0: return '.'      # free
    if n == 0xFF7: return 'X'  # bad
    if n >= 0xFF8: return 'o'  # allocated (last in chain)
    return 'O'                 # allocated

def clusterGraphType16(n):
    if n == 0: return '.'       # free
    if n == 0xFFF7: return 'X'  # bad
    if n >= 0xFFF8: return 'o'  # allocated (last in chain)
    return 'O'                  # allocated

def clusterGraphType32(n):
    if n == 0: return '.'           # free
    if n == 0xFFFFFFF7: return 'X'  # bad
    if n >= 0xFFFFFFF8: return 'o'  # allocated (last in chain)
    return 'O'                      # allocated

clusterGraphType = {12:clusterGraphType12, 16:clusterGraphType16, 32:clusterGraphType32}


class RawDrive:
    def __init__(self, drive):
        self.drive = drive
        self.dev = file('\\\\?\\' + self.drive, 'rb')
        self.sigAt510 = ''  # should be '\x55\xAA'
        self.bs, bs32 = self.getBootSector()

        # always 0 for FAT32
        self.RootDirSectors = ((self.bs.BPB_RootEntCnt * 32) + (self.bs.BPB_BytsPerSec - 1)) / self.bs.BPB_BytsPerSec
        # size of each FAT in sectors
        # (note that only the first CountofClusters+2 entries are used)
        self.FATSz = self.bs.BPB_FATSz16 or bs32.BPB_FATSz32
        #######self.FATSz = self.bs.BPB_FATSz16
        self.FirstDataSector = self.bs.BPB_ResvdSecCnt + (self.bs.BPB_NumFATs * self.FATSz) + self.RootDirSectors;
        self.TotSec = self.bs.BPB_TotSec16 or self.bs.BPB_TotSec32
        self.DataSec = self.TotSec - (self.bs.BPB_ResvdSecCnt + (self.bs.BPB_NumFATs * self.FATSz) + self.RootDirSectors)
        # count of available data clusters (note that indexes start at 2, so index range is [2..CountofClusters+1])
        self.CountofClusters = self.DataSec / self.bs.BPB_SecPerClus
        # FAT type depends solely on count of data clusters
        self.FATEntryBits = (12 if self.CountofClusters < 4085 else
                             16 if self.CountofClusters < 65525 else
                             32)

        if self.FATEntryBits == 32:
            self.bs = bs32

    def getBootSector(self):
        try:
            reqByteCnt = 512
            self.dev.seek(0)
            s = self.dev.read(reqByteCnt)
            if len(s) != reqByteCnt:
                raise IOError('Reading returned %d bytes instead of %d.' % (len(s), reqByteCnt))
        except IOError, x:
            raise DriveError('Could not read boot sector of drive %s - %s' % (self.drive, str(x)))
        self.sigAt510 = s[-2:]
        return getStruct(common + fat1216, s), getStruct(common + fat32, s)

    def getSectors(self, start, count):
        bytes = count * self.bs.BPB_BytsPerSec
        self.dev.seek(start * self.bs.BPB_BytsPerSec)
        ret = self.dev.read(bytes)
        if len(ret) != bytes:
            raise DriveError('Could not read %d sectors, starting at sector %d' % (count, start))
        return ret

    def getFATs(self):    
        ret = []
        bitsPerFAT = (self.CountofClusters + 2) * self.FATEntryBits
        bytesPerFAT = (bitsPerFAT + 7) / 8
        sector = self.bs.BPB_ResvdSecCnt
        for i in range(self.bs.BPB_NumFATs):
            s = self.getSectors(sector, self.FATSz)[:bytesPerFAT]
            # make sure the last 4 bits are 0
            # iff it's FAT12 and the last entry doesn't exactly end on a byte
            if self.FATEntryBits == 12 and bitsPerFAT % 8 != 0:
                s = s[:-1] + chr(ord(s[-1]) & 0x0F)
            ret += [s]
            sector += self.FATSz
        return ret

    def dumpGeneric(self):
        print 'Volume type is FAT' + str(self.FATEntryBits)
        print 'Count of data clusters:', self.CountofClusters
        print

    def dumpBootSector(self):
        print 'Common:'
        print 'OEM name             ', repr(self.bs.BS_OEMName)
        print 'bytes/sector         ', self.bs.BPB_BytsPerSec
        print 'sectors/cluster      ', self.bs.BPB_SecPerClus
        print 'reserved sectors     ', self.bs.BPB_ResvdSecCnt
        print 'FATs                 ', self.bs.BPB_NumFATs
        print 'root entries         ', self.bs.BPB_RootEntCnt
        print 'total sectors (16)   ', self.bs.BPB_TotSec16
        print 'media                ', self.bs.BPB_Media
        print 'sectors/FAT (16)     ', self.bs.BPB_FATSz16
        print 'sectors/track (INT13)', self.bs.BPB_SecPerTrk
        print 'heads (INT13)        ', self.bs.BPB_NumHeads
        print 'hidden sectors       ', self.bs.BPB_HiddSec
        print 'total sectors (32)   ', self.bs.BPB_TotSec32
        print

        if self.FATEntryBits == 32:
            pass
        else:
            print 'FAT12/16:'
            print 'drive number    ', self.bs.BS_DrvNum
            print 'reserved        ', self.bs.BS_Reserved1
            print 'boot sig        ', self.bs.BS_BootSig
            print 'volume ID       ', hex(self.bs.BS_VolID)
            print 'volume label    ', self.bs.BS_VolLab
            print 'file system type', self.bs.BS_FilSysType
            

    def dumpFATs(self):
        fats = self.getFATs()
        print 'FAT count:', len(fats)
        sigs = {}
        for i in range(len(fats)):
            sig = hashlib.md5(fats[i]).hexdigest()
            print 'FAT 0x%02X MD5: %s' % (i, sig)
            if sig in sigs:
                sigs[sig] += [i]
            else:
                sigs[sig] = [i]
        print
        for k in sigs:
            fatIndexes = sigs[k]
            print 'FAT(s):', ', '.join(['0x%02X' % i for i in fatIndexes])
            bitmap = fats[fatIndexes[0]]
            entries = self.getFATEntries(bitmap, self.CountofClusters + 2, self.FATEntryBits)
            outputWidth = 64
            #print '*'
            for i in xrange(0, len(entries), outputWidth):
                s = self.getFATGraphRow(entries[i:i+outputWidth])
                if i == 0:
                    print '  ' + s[2:]
                else:
                    print s
                    
        
    def getFATEntries(self, bitmap, count, bits):
        if len(bitmap) != (count*bits + 7) / 8:
            raise DriveError('Invalid FAT size in getFATEntries()')
        ret = []
        if bits == 12:
            pairs = count / 2
            i = 0
            for n in xrange(pairs):
                triad = valUInt(bitmap[i:i+3])
                ret += [triad & 0xFFF, triad >> 12]
                i += 3
            if count % 2 != 0:
                triad = valUInt(bitmap[i:i+3])
                ret += [triad & 0xFFF]
        elif bits == 16:
            for i in xrange(0, count*2, 2):
                ret += [valUInt(bitmap[i:i+2])]
        elif bits == 32:
            for i in xrange(0, count*4, 4):
                ret += [valUInt(bitmap[i:i+4])]
        else:
            raise DriveError('Invalid FAT entry size in getFATEntries(): %d', bits)
        return ret
    

    def getFATGraphRow(self, entries):
        func = clusterGraphType[self.FATEntryBits]
        return ''.join([func(n) for n in entries])


def main(args):
    if '/?' in args:
        help()
        sys.exit(0)
        
    dispBoot = False
    dispFAT = False
    drives = []
    for s in args:
        if s.upper() == '/B':
            dispBoot = True
        elif s.upper() == '/F':
            dispFAT = True
        elif s[:1] == '/':
            printErrLn('Invalid switch: ' + s)
            sys.exit(1)
        else:
            drv = os.path.splitdrive(s)[0]
            if not drv:
                printErrLn('Invalid drive: ' + s)
                sys.exit(1)
            drives += [drv]
    
    for d in drives:
        show(d, dispBoot, dispFAT)
        

def help():
    print """\
File system information tool.

FAT drives /B /F

  drive  The list of drives to check.
  /B     Show boot sector information.
  /F     Show FAT table information.\
"""
    

def printErrLn(s):
    sys.stderr.write(s)
    sys.stderr.write('\n')


def show(drive, dispBoot, dispFAT):
    print 'Drive', drive
    try:
        drv = RawDrive(drive)
        drv.dumpGeneric()
        if dispBoot:
            drv.dumpBootSector()
        if dispFAT:
            drv.dumpFATs()
    except DriveError, x:
        print x


main(sys.argv[1:])


##    A FAT file system volume is composed of four basic regions, which are
##    laid out in this order on the volume:
##        
##    0 - Reserved Region
##    1 - FAT Region
##    2 - Root Directory Region (doesn't exist on FAT32 volumes)
##    3 - File and Directory Data Region


##    size    tracks  sectors sides   capacity
##    5.25    40      8       1       160
##    5.25    40      9       1       180
##    5.25    40      8       2       320
##    5.25    40      9       2       360
##    5.25    80      15      2       1200
##    3.5     80      9       2       720
##    3.5     80      18      2       1440
##    3.5     80      36      2       2880
