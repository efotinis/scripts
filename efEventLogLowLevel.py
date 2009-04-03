"""Low level NT Event Log.

Provide binary read access to Windows NT event logs.
Intended for non-Windows platforms or for improperly closed (dirty) logs.

For live event logs in Windows, use efEventLog instead.
"""

import struct


class BinFile:
    """Binary file read helper."""

    class Error(Exception):
        def __init__(self, msg):
            Exception.__init__(self, msg)

    def __init__(self, name):
        self.f = None
        self.f = file(name, 'rb')

    def __del__(self):
        self.close()

    def close(self):
        if self.isOpen():
            self.f.close()
            self.f = None

    def isOpen(self):
        return self.f is not None

    def readBytes(self, n):
        """Read exactly n bytes."""
        s = self.f.read(n)
        if len(s) < n:
            raise self.Error('EOF encountered')
        return s

    def readStruct(self, fmt):
        """Read a Python.struct."""
        n = struct.calcsize(fmt)
        s = self.readBytes(n)
        return struct.unpack(fmt, s)

    class Dummy:
        pass

    def readObject(self, reader):
        """Read a struct and create an object using an ObjectReader."""
        t = self.readStruct(reader.fmt)
        obj = self.Dummy()
        for name, value in zip(reader.names, t):
            setattr(obj, name, value)
        return obj

    def atEof(self):
        """Check whether current pos is on or beyond EOF."""
        pos = self.f.tell()
        self.f.seek(0, 2)
        size = self.f.tell()
        self.f.seek(pos)
        return pos >= size

    def skipRec(self):
        (n,) = self.readStruct('L')
        self.f.seek(n - 4, 1)

    def getRec(self):
        (n,) = self.readStruct('L')
        self.f.seek(-4, 1)
        return self.readBytes(n)


class StructReader:

    def __init__(self, fields):
        self.fmt = ''.join(f[0] for f in fields)
        self.names = tuple(f[1] for f in fields)

    class Dummy:
        pass

    def build(self, s):
        values = struct.unpack(self.fmt, s)
        obj = self.Dummy()
        for name, value in zip(self.names, values):
            setattr(obj, name, value)
        return obj

    def read(self, f):        
        n = struct.calcsize(self.fmt)
        s = f.readBytes(n)
        return self.build(s)


headerReader = StructReader(
    (
        ('L', 'HeaderSize'),
        ('L', 'Signature'),
        ('L', 'MajorVersion'),
        ('L', 'MinorVersion'),
        ('L', 'StartOffset'),
        ('L', 'EndOffset'),
        ('L', 'CurrentRecordNumber'),
        ('L', 'OldestRecordNumber'),
        ('L', 'MaxSize'),
        ('L', 'Flags'),
        ('L', 'Retention'),
        ('L', 'EndHeaderSize')
    )
)

eofReader = StructReader(
    (
        ('L', 'RecordSizeBeginning'),
        ('L', 'One'),
        ('L', 'Two'),
        ('L', 'Three'),
        ('L', 'Four'),
        ('L', 'BeginRecord'),
        ('L', 'EndRecord'),
        ('L', 'CurrentRecordNumber'),
        ('L', 'OldestRecordNumber'),
        ('L', 'RecordSizeEnd')
    )
)

# NOTE: EventID should be unsigned, but in32evtlog.ReadEventLog returns it as signed...
recordReader = StructReader(
    (
        ('L', 'Length'),
        ('L', 'Reserved'),
        ('L', 'RecordNumber'),
        ('L', 'TimeGenerated'),
        ('L', 'TimeWritten'),
        ('L', 'EventID'),
        ('H', 'EventType'),
        ('H', 'NumStrings'),
        ('H', 'EventCategory'),
        ('H', 'ReservedFlags'),
        ('L', 'ClosingRecordNumber'),
        ('L', 'StringOffset'),
        ('L', 'UserSidLength'),
        ('L', 'UserSidOffset'),
        ('L', 'DataLength'),
        ('L', 'DataOffset')
    )
)

##    fixedEventFields = (
##        ('4s', 'Reserved'), # (sig) Used by the service
##        ('l', 'RecordNumber'), # Absolute record number
##        ('l', 'TimeGenerated'), # Seconds since 1-1-1970
##        ('l', 'TimeWritten'), # Seconds since 1-1-1970
##        ('l', 'EventID'),
##        ('h', 'EventType'),
##        ('h', 'NumStrings'),
##        ('h', 'EventCategory'),
##        ('h', 'ReservedFlags'), # For use with paired events (auditing)
##        ('l', 'ClosingRecordNumber'), # For use with paired events (auditing)
##        ('l', 'StringOffset'), # Offset from beginning of record
##        ('l', 'UserSidLength'),
##        ('l', 'UserSidOffset'),
##        ('l', 'DataLength'),
##        ('l', 'DataOffset')) # Offset from beginning of record
    

SIG = 0x654c664c  # record sig; ASCII 'eLfL'
HEADER_SIZE = 0x30
EOF_SIZE = 0x28

# header flags
ELF_LOGFILE_HEADER_DIRTY = 0x1
ELF_LOGFILE_HEADER_WRAP = 0x2
ELF_LOGFILE_LOGFULL_WRITTEN = 0x4
ELF_LOGFILE_ARCHIVE_SET = 0x8 


def fieldsFmt(fields):
    return ''.join(f[0] for f in fields)


def getUnicodeStr(bytes, i):
    """Extract a LPWCSTR from 'bytes' at pos 'i'.

    Return the extracted string and the position past the terminating NUL.
    """
    iend = len(bytes)
    ret = u''
    while i < iend - 2:
        c0, c1 = ord(bytes[i]), ord(bytes[i+1])
        i += 2
        if c0 == c1 == 0:
            break
        ret += unichr(c0 + c1*256)
    else:
        raise Exception('no NUL terminator found')
    return ret, i


import pywintypes
def toTime(n):
    """Convert an event log time DWORD to a PyTime (if avail.) or (smth else...)."""
    # n is seconds since 00:00:00 1970-01-01 UTC
    return pywintypes.Time(n)  # TODO: is this local or UTC ???


def toSid(s):
    return pywintypes.SID(s)


class Reader(BinFile):
    """Low-level read access to an NT event log."""

    class Error(BinFile.Error):
        def __init__(self, msg):
            BinFile.Error.__init__(self, msg)

    def __init__(self, name):
        BinFile.__init__(self, name)
        self.hdr = self._readHeader()
        self.f.seek(self.hdr.EndOffset)
        self.eof = self._readEof()

    def _readHeader(self):
        hdr = self.readObject(headerReader)
        if hdr.HeaderSize <> HEADER_SIZE or hdr.EndHeaderSize <> HEADER_SIZE:
            raise self.Error('bad header size')
        if hdr.Signature <> SIG:
            raise self.Error('bad header sig')
        if hdr.MajorVersion <> 1 or hdr.MinorVersion <> 1:
            raise self.Error('bad file version')
        return hdr

    def _readEof(self):
        eof = self.readObject(eofReader)
        if eof.RecordSizeBeginning <> EOF_SIZE or eof.RecordSizeEnd <> EOF_SIZE:
            raise self.Error('bad eof size')
        if (eof.One, eof.Two, eof.Three, eof.Four) <> (0x11111111, 0x22222222, 0x33333333, 0x44444444):
            raise self.Error('bad eof sig')
        return eof

    def getOldest(self):
        """Get the recno of the oldest event."""
        return self.hdr.OldestRecordNumber

    def getCount(self):
        """Get the count of events."""
        if self.hdr.OldestRecordNumber:
            return self.hdr.CurrentRecordNumber - self.hdr.OldestRecordNumber
        else:
            return 0

    def read(self, flags, recno=None):
        """Return a one-element list of a record (or an empty list on end).

        The list is used to match the interface of efEventLog.Reader."""
        pass

    def __getitem__(self, i):
        """(Tmp func to) read the i'th event record (note: i is pos, not id)."""
        if i < 0:
            i += self.getCount()
        if i < 0 or i >= self.getCount():
            raise IndexError

        LAME_SEQUENTIAL_OPTIMIZATION = True
        if LAME_SEQUENTIAL_OPTIMIZATION:
            if i == 0:
                self.f.seek(self.hdr.StartOffset)
        else:
            self.f.seek(self.hdr.StartOffset)
            for n in range(i):
                self.skipRec()

        s = self.getRec()

        # extract the fixed fields
        n = struct.calcsize(recordReader.fmt)
        rec = recordReader.build(s[:n])
        (trailSize,) = struct.unpack('L', s[-4:])
        ##print len(s), rec.Length, trailSize
        if rec.Length <> trailSize:
            raise self.Error('record lead/trail size mismatch')
        if rec.Reserved <> SIG:
            raise self.Error('bad record sig')
        
        class Dummy:
            pass
        obj = Dummy

        
        obj.Reserved = rec.Reserved
        obj.RecordNumber = rec.RecordNumber
        obj.TimeGenerated = toTime(rec.TimeGenerated)
        obj.TimeWritten = toTime(rec.TimeWritten)
        obj.EventID = rec.EventID
        obj.EventType = rec.EventType
        obj.EventCategory = rec.EventCategory
        obj.ReservedFlags = rec.ReservedFlags
        obj.ClosingRecordNumber = rec.ClosingRecordNumber

        i = n
        obj.SourceName, i = getUnicodeStr(s, i)
        obj.ComputerName, i = getUnicodeStr(s, i)

        if rec.UserSidLength:
            i, j = rec.UserSidOffset, rec.UserSidLength
            obj.Sid = toSid(s[i:i+j])
        else:
            obj.Sid = None

        if rec.NumStrings:
            obj.StringInserts = []
            i = rec.StringOffset
            for n in range(rec.NumStrings):
                strIns, i = getUnicodeStr(s, i)
                obj.StringInserts += [strIns]
            obj.StringInserts = tuple(obj.StringInserts)
        else:
            obj.StringInserts = None

        if rec.DataOffset:
            i, j = rec.DataOffset, rec.DataLength
            obj.Data = s[i:i+j]
        else:
            obj.Data = None

        return obj


##    def readRecord(self):
##        (size,) = f.readStruct('l')
##        s = f.readBytes(size - 8)
##        if f.readStruct('l')[0] <> size:
##            raise SavedEventLog.Error('trailing size mismatch')
##        return s
##        
##    def readEvent(self):
##        s = self.readRecord()
##
##        fixFldfmt = '=' + fieldsFmt(SavedEventLog.fixedEventFields)
##        n = struct.calcsize(fixFldfmt)
##        ret = SavedEventLog.Rec(SavedEventLog.fixedEventFields, s[:n])
##        if ret.Reserved <> 'LfLe':
##            raise SavedEventLog.Error('bad event sig')
##
##        ##############
##        i = n
##        tmp, i = getUnicodeStr(s, i)
##        setattr(ret, 'source', tmp)
##        tmp, i = getUnicodeStr(s, i)
##        setattr(ret, 'computer', tmp)
##
##        i, j = ret.UserSidOffset, ret.UserSidLength
##        i -= 4
##        setattr(ret, 'sid', s[i:i+j])
##
##        setattr(ret, 'strings', [])
##        i = ret.StringOffset
##        i -= 4
##        for n in range(ret.NumStrings):
##            tmp, i = getUnicodeStr(s, i)
##            ret.strings += [tmp]
##
##        i, j = ret.DataOffset, ret.DataLength
##        i -= 4
##        setattr(ret, 'data', s[i:i+j])
##
##        return ret


    # context management (with stmt)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


###fname, system = 'security.evt', None
##fname, system = 'SysEvent (vm).Evt', u'efxpsp2'
##
##print
##f = SavedEventLog(fname)
##hdr = f.readHeader()
##
####sids = set()
##
##for n in range(hdr.dataRecCntPlusOne - 1):
##    evt = f.readEvent()
##    #print evt.strings
####    sids.add(evt.sid)
###ftr = f.readFooter()


##sidTypes = {
##    win32security.SidTypeUser: 'user',
##    win32security.SidTypeGroup: 'group',
##    win32security.SidTypeDomain: 'domain',
##    win32security.SidTypeAlias: 'alias',
##    win32security.SidTypeWellKnownGroup: 'well-known group',
##    win32security.SidTypeDeletedAccount: 'deleted account',
##    win32security.SidTypeInvalid: 'invalid',
##    win32security.SidTypeUnknown: 'unknown',
##    win32security.SidTypeComputer: 'computer'
##    }
##
##import win32security
##for s in sids:
##    if not s:
##        print '<no sid>'
##    else:
##        sid = win32security.SID(s)
##        name, domain, type = win32security.LookupAccountSid(system, sid)
##        print repr(name), repr(domain), sidTypes[type]
##    print '\t', repr(s)
    

##el = EventLog('efxpsp2', 'System')
##print el.getCount()


if __name__ == '__main__':
    log = Reader(r'D:\WORK\event logs\security.evt')
    print log.getOldest(), log.getCount()
    n = 0
    for i in range(log.getCount()):
        x = log[i]
        pass
    print n
