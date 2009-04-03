# Copyright (C) Elias Fotinis 2006-2007
# All rights reserved.
#
# History:
#   2006-01-12: Created.
#   2007-03-08: Replaced various sys.exit's with exceptions.
#               Replace option map with Options class.
#               Mulitple hash type support via /T switch;
#                 initially only MD5 was supported.
#   2007-06-22: Added CRC(32) support and /I switch.
#               Added check 
#
# Bugs:
# - console_stuff.SamePosOutput() sometimes causes output to start at column 1
#   instead of 0. Probably due to print's internal sep. guessing (2007-03-08).
#   FIXED: s. BUGFIX #1
#
# Todo:
# - Only allow DOS-style wildcards by default.
#   Add a switch (/G) to allow globbing (2007-03-08).
# - Add a switch for strict error checking (should exit with EXIT_ERROR
#   on the first range or file error).


import os
import sys
import hashlib
import binascii
import struct
import re
import glob

import console_stuff

EXIT_OK = 0
EXIT_ERROR = 1  # currently unused
EXIT_BAD_PARAM = 2


def showHelp():
    """Show help screen."""
    print """\
File hash calculator.  (C) Elias Fotinis 2006-2007

FSIG [/T:type] [/O:offset] [/L:length] [/B:bufsize] [/U] [/NP] files...

  /T     Hash type. One of: CRC(32),MD5,SHA1,SHA224,SHA256,SHA384,SHA512.
         Default is MD5.
  /O     Starting file offset. Default is 0.
  /L     Number of bytes to process. Default is -1, meaning all.
  /B     Read buffer size. Default is 64K.
  /U     Output uppercase hex digits.
  /I     Invert output, displaying the name first and then the hash.
         Useful for creating SFV files.
  /NP    Do not display progress indicator. This is the default when STDOUT is
         not the console.
  files  List of files. Glob wildcards allowed.

Size and offset values can have a size unit of K, M or G (e.g. '64K', '1M').
Returns 0 on success, 1 on error, 2 on invalid options."""


def main(args):
    """Parse cmdline and loop through files."""
    if '/?' in args:
        showHelp()
        return EXIT_OK

    try:
        opt = Options(args)
    except (Options.Error, ValueError), x:
        errLn(str(x))
        return EXIT_BAD_PARAM
        
    if not opt.files:
        errLn('No files specified.')
        return EXIT_BAD_PARAM

    for s in opt.files:
        files = glob.glob(s)
        files = [s for s in files if os.path.isfile(s)]  # files only
        if not files:
            errLn('No files match "%s"' % s)
            continue
        for file in files:
            fileSig(file, opt)

    return EXIT_OK


def fsize(f):
    oldPos = f.tell()
    f.seek(0, 2)
    ret = f.tell()
    f.seek(oldPos)
    return ret

    
def bytesToRead(f, offset, length):
    fs = fsize(f)
    if offset < 0:
        offset = 0
    if offset > fs:
        offset = fs
    if length < 0:
        length = fs - offset
    end = offset + length
    if end > fs:
        end = fs
    return end - offset


def fileSig(s, opt):
    """Calc and disp file MD5 or an I/O error msg."""
    try:
        f = open(s, 'rb')
        if opt.progress:
            progressBytesToRead = bytesToRead(f, opt.offset, opt.length)
            progressBytesRead = 0
            progressChars = ('/', '-', '\\', '|')
            progressCharI = 0
            print s, '... ',
            spo = console_stuff.SamePosOutput()
        f.seek(opt.offset)
        d = opt.hashFactory()
        bytesToGo = opt.length
        while bytesToGo != 0:
            buf = f.read(opt.buflen)
            if buf == '': break
            if bytesToGo != -1 and len(buf) > bytesToGo:
                buf = buf[:bytesToGo]
            d.update(buf)
            if opt.progress:
                progressBytesRead += len(buf)
                spo.restore()
                percent = (progressBytesRead*100/progressBytesToRead
                           if progressBytesToRead else 0)
                print str(percent) + '%', progressChars[progressCharI]
                progressCharI += 1
                if progressCharI >= len(progressChars):
                    progressCharI = 0
            if bytesToGo != -1:
                bytesToGo = bytesToGo - len(buf)
        if opt.progress:
            spo.pos.X = 0
            spo.restore(True)
        if bytesToGo > 0:
            print 'Reached EOF while reading "%s"' % s
        else:
            digest = d.hexdigest()
            if opt.ucase:
                digest = digest.upper()
            sys.stdout.write('')  # BUGFIX #1
            if opt.invert:
                print s, digest
            else:
                print digest, s
    except IOError, x:
        fname = x.filename
        if fname is None:
            fname = s
        errLn(x.strerror + ': ' + s)
        

def errLn(s):
    """Print a line in STDERR."""
    sys.stderr.write('ERROR: ' + s + '\n')


class Options:

    def __init__(self, args):
        hashType = 'MD5'
        self.hashFactory = None  # will be set later
        self.offset = 0
        self.length = -1
        self.buflen = 64 * 1024
        self.progress = True
        self.ucase = False
        self.invert = False
        self.files = []
        switchRx = re.compile(r'/([^:]+)(?::(.*))?', re.I)
        for s in args:
            m = switchRx.match(s)
            if not m:
                self.files.append(s)
                continue
            sw = m.group(1).upper()
            val = m.group(2) or ''
            if sw == 'T':
                hashType = val.upper()
                types = 'CRC,CRC32,MD5,SHA1,SHA224,SHA256,SHA384,SHA512'.split(',')
                if hashType not in types:
                    raise Options.BadValueError(sw, 'type', val)
            elif sw == 'O':
                self.offset = getSizeParam(val)
                if self.offset < 0:
                    raise Options.BadValueError(sw, 'offset', val)
            elif sw == 'L':
                self.length = getSizeParam(val)
                if self.length < -1:
                    raise Options.BadValueError(sw, 'length', val)
            elif sw == 'B':
                self.buflen = getSizeParam(val)
                if self.buflen <= 0:
                    raise Options.BadValueError(sw, 'buffer size', val)
            elif sw == 'NP':
                self.progress = False
            elif sw == 'U':
                self.ucase = True
            elif sw == 'I':
                self.invert = True
            else:
                raise Options.BadSwitchError(sw)
        if hashType in ('CRC','CRC32'):
            self.hashFactory = crc32digest
        else:
            class HashFactory:
                def __init__(self, type):
                    self.type = type
                def __call__(self):
                    return hashlib.new(self.type)
            self.hashFactory = HashFactory(hashType)
        if not console_stuff.iscon():
            self.progress = False

    class Error(Exception):
        pass

    class BadValueError(Error):
        def __init__(self, switch, switchName, value):
            self.switch = switch
            self.switchName = switchName
            self.value = value
        def __str__(self):
            t = (self.switch, self.switchName, self.value)
            return 'Bad value for /%s (%s): "%s"' % t

    class BadSwitchError(Error):
        def __init__(self, switch):
            self.switch = switch
        def __str__(self):
            return 'Bad switch: "%s"' % self.switch


## TODO: replace this with cmdLineOptions.parseSize
def getSizeParam(s):
    """Parse a size (any base) with optional unit or abort."""
    if not s:
        raise ValueError('Missing int value.')

    # extract size factor
    factor = 1
    units = 'KMG'
    unitIndex = units.find(s[-1].upper())
    if unitIndex >= 0:
        factor = 1024 ** (1 + unitIndex)
        s = s[:-1]

    try:
        x = float(s) if '.' in s else int(s, 0)
        return int(x * factor)
    except:
        raise ValueError('Invalid number: "%s"' % s)
        

class crc32digest:
    """A CRC32 digest using the hashlib object interface."""
    digest_size = 32
    def __init__(self, data=''):
        self.value = binascii.crc32(data)
    def update(self, data):
        self.value = binascii.crc32(data, self.value)
    def digest(self):
        return struct.pack('>L', self.value & 0xffffffff)
    def hexdigest(self):
        return binascii.hexlify(self.digest())
    def copy(self):
        ret = crc32digest()
        ret.value = self.value
        return ret


sys.exit(main(sys.argv[1:]))
