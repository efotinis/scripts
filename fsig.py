# File hash calculator.
#
# TODO: only allow DOS-style wildcards by default (add switch -g for explicit globbing)
# - Add a switch for strict error checking (exit on first range or file error).
# TODO: report glob patterns that match no files (currently they are silently ignored)

import os
import sys
import hashlib
import binascii
import struct
import re
import glob
import itertools
import optparse
import copy

import console_stuff
import fileutil
import CommonTools
import optparseutil


HASH_TYPES = 'crc32 md5 sha1 sha224 sha256 sha384 sha512'.split()

DEFAULT_HASH_TYPE = 'md5'
DEFAULT_BUFFER_SIZE = 64 * 1024


class CustomOption(optparse.Option):
    """Extended optparse Option class which includes a 'size' type."""
    TYPES = optparse.Option.TYPES + ('size',)
    TYPE_CHECKER = copy.copy(optparse.Option.TYPE_CHECKER)
    TYPE_CHECKER['size'] = optparseutil.check_size


class Crc32:
    """CRC32 digest using the hashlib interface."""
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
        ret = Crc32()
        ret.value = self.value
        return ret


def getopt():
    parser = optparse.OptionParser(
        description='Calculate file hashes.',
        usage='%prog [options] FILES...',
        epilog='Glob wildcards allowed in FILES. '
               'Size and offset values can have a size unit (one of "KMGTPEZY"), e.g. "64K", "0.5m".',
        add_help_option=False,
        option_class=CustomOption)

    typeslist = HASH_TYPES[:]
    i = typeslist.index(DEFAULT_HASH_TYPE)
    typeslist[i] += ' (default)'
    typeslist = ', '.join(typeslist)

    _add = parser.add_option
    _add('-t', dest='hashFactory', default=DEFAULT_HASH_TYPE, metavar='TYPE',
         help='Hash type. Available options: ' + typeslist)
    _add('-o', dest='offset', type='size', default=0,
         help='Starting file offset. Default is 0.')
    _add('-l', dest='length', type='size', default=-1,
         help='Number of bytes to process. Default is -1, meaning all.')
    _add('-b', dest='buflen', type='size', default=DEFAULT_BUFFER_SIZE,
         help='Read buffer size. Default is %default.')
    _add('-u', dest='ucase', action='store_true',
         help='Output uppercase hex digits.')
    _add('-i', dest='invert', action='store_true',
         help='Invert output, displaying the file name first. '
              'Useful for creating SFV files.')
    _add('-v', dest='verify', 
         help='List of comma-separated hashes to check against the specified files.')
    _add('--np', dest='progress', action='store_false', default=True,
         help='Do not display progress indicator. '
              'This is automatically set when STDOUT is not a console.')
    _add('-?', action='help', help='This help.')

    opt, args = parser.parse_args()

    if not console_stuff.iscon():
        opt.progress = False

    if opt.offset < 0:
        parser.error('offset must be >= 0')
    if opt.length < -1:
        parser.error('number of bytes must be >= -1')
    if opt.buflen <= 0:
        parser.error('buffer size must be > 0')

    opt.hashFactory = opt.hashFactory.lower()
    if opt.hashFactory not in HASH_TYPES:
        parser.error('invalid hash type: "%s"' % opt.hashFactory)
    if opt.hashFactory == 'crc32':
        opt.hashFactory = Crc32
    else:
        class HashFactory:
            def __init__(self, type):
                self.type = type
            def __call__(self):
                return hashlib.new(self.type)
        opt.hashFactory = HashFactory(opt.hashFactory)

    if opt.verify:
        strsize = opt.hashFactory().digest_size * 2
        a = []
        for s in opt.verify.split(','):
            if len(s) != strsize:
                parser.error('invalid verify hash size: "%s"' % s)
            try:
                a += [int(s, 16)]
            except ValueError:
                parser.error('invalid verify hash: "%s"' % s)
        opt.verify = a

    parser.destroy()
    return opt, map(unicode, args)


def calc_read_size(fsize, offset, length):
    """Calculate the actual byte count given the file size and read offset/length."""
    if offset < 0:
        offset = 0
    if offset > fsize:
        offset = fsize
    if length < 0:
        length = fsize - offset
    end = offset + length
    if end > fsize:
        end = fsize
    return end - offset


def fileSig(s, opt, verify=None):
    """Calculate and print file hash.

    If 'verify' is set, tests and prints whether hash matches.
    """
    try:
        f = open(s, 'rb')
        if opt.progress:
            progressBytesToRead = calc_read_size(fileutil.fsize(f), opt.offset, opt.length)
            progressBytesRead = 0
            spinner = itertools.cycle('/-\\|')
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
                print str(percent) + '%', spinner.next()
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
            # the empty write() prevents SamePosOutput from
            # accidentally printing at col 1 (instead of 0)
            sys.stdout.write('')

            if verify:
                digest = '   OK   ' if verify == int(digest, 16) else '**FAIL**'
            
            if opt.invert:
                print s, digest
            else:
                print digest, s
    except IOError as x:
        fname = x.filename
        if fname is None:
            fname = s
        CommonTools.errln(x.strerror + ': ' + s)


def files_gen(a):
    """Generate file paths from list of file glob patterns."""
    for pattern in a:
        for s in glob.glob(pattern):
            if os.path.isfile(s):
                yield s
        

if __name__ == '__main__':
    opt, args = getopt()

    filepaths = list(files_gen(args))
    if not filepaths:
        CommonTools.exiterror('no files specified', 2)

    if opt.verify:
        if len(opt.verify) != len(filepaths):        
            CommonTools.exiterror('number of specified verify hashes does not match file count', 2)
        for s, sig in zip(filepaths, opt.verify):
            fileSig(s, opt, verify=sig)
    else:
        for s in filepaths:
            fileSig(s, opt)
